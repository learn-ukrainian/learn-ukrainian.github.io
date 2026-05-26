# Bio Decolonization Checklist

**Purpose**: every bio module (and its wiki article) must pass this checklist before acceptance. Catches Russocentric framing, Russian-imperial transliteration, Russocentric periodization, Soviet-era propaganda terminology leaking in uncritically, and source-tier policy violations.

**Used by**: Phase 5 Q1 ticket #2336 (decolonization pass, DeepSeek-pro hermes), plus inline by writers in Phase 2 (plan YAMLs) and Phase 4 (wiki articles).

**Companion docs**:
- `docs/audits/bio-track-gap-audit-2026-05-26.md` — the SSOT scope
- `docs/best-practices/bio-research-source-tiers.md` (#2312) — source authority tiers
- `docs/best-practices/bio-naming-canonical.md` (#2313) — naming + transliteration rules
- `docs/best-practices/politically-charged-bios.md` (#2311) — politically-charged framing

---

## A. Russocentric framing

Flag any of these unless the bio is *explicitly* analyzing the framing itself:

| Pattern | Why it fails | Acceptable form |
|---|---|---|
| "Russian poet of Ukrainian origin" | Erases UA identity by primary identification | "Ukrainian poet" |
| "Малороссия" / "Малоросія" used non-historically | Russian-imperial term denying UA statehood | "Україна" |
| "Юго-Западный край" used non-historically | Same | "Україна" / "Right-Bank Ukraine" |
| "Russian Civil War 1917-1922" framing UA events | Erases the Ukrainian Revolution | "Українська революція 1917-1921" / "Soviet-Ukrainian War" |
| "Soviet republic" without context that USSR was occupation | Reinforces legitimation framing | "Ukrainian SSR (under Soviet occupation)" where context warrants |
| "Russia" used for "Soviet Union" or "Russian Empire" without specificity | Conflates three distinct regimes | Specify: "Russian Empire", "Soviet Union", "Russian Federation" |
| "USSR liberated [city]" 1944 framing | Soviet propaganda framing | "Soviet forces re-occupied [city]" or factual military framing |
| "Brought into the fold of the Russian people" | Imperial-Russian rhetoric | Re-phrase factually |
| Author called "Russian" because lived under Russian Empire | Imperial-era nationality ≠ ethnic identity | "Lived under Russian Imperial rule; wrote in Ukrainian" |

## B. Transliteration — Russian-imperial leaking in

Per `bio-naming-canonical.md` (#2313 — BGN/PCGN 2010):

| Forbidden (Russian-imperial / French-via-Russian) | Correct |
|---|---|
| Chevtchenko | Shevchenko |
| Kiev (in modern context) | Kyiv |
| Kharkov | Kharkiv |
| Lvov | Lviv |
| Khmielnitski | Khmelnytsky |
| Tcherkassy / Tcherkasy | Cherkasy |
| Petlioura | Petliura |
| Bandera (in RU "Bandyera") | Bandera |
| Russian patronymic form used for Ukrainian figure (e.g. "Тарас Григорьевич Шевченко" in body text) | UA form ("Тарас Григорович Шевченко") |

**Historical-quotation exception**: if quoting a primary source that uses Russian-imperial spelling, retain it inside the quote marks but always provide the canonical UA form in the surrounding text.

## C. Periodization

| Russocentric term | Replace with |
|---|---|
| "Voluntary unification with Russia 1654" | "Pereiaslav Agreement 1654 (military alliance, subsequently re-interpreted by Russia as 'unification')" |
| "Time of Troubles" used for UA history | Ukrainian historical periodization |
| "Civil War 1917-1921" (when discussing UA events) | "Ukrainian Revolution 1917-1921" |
| "Great Patriotic War" | "Second World War" / "WWII" (Soviet-era propaganda term) |
| "Years of stagnation" | "Brezhnev era" (Soviet propaganda term) |
| "Western Ukraine annexed 1939" | "Western Ukraine occupied 1939" (legal status complex; ≠ legitimate annexation) |
| "Voluntary collectivization" | "Forced collectivization" |
| "Famine of 1932-33" without naming | "Голодомор / Holodomor 1932-33" (recognized genocide) |

## D. Russianisms in Ukrainian-language body text

Defer to existing audit pipeline:
- `mcp__sources__check_russian_shadow` for words
- VESUM verification per `mcp__sources__verify_word(s)` for stress/forms
- Style-guide search via `mcp__sources__search_style_guide`

But explicitly flag these category-level issues even if individual words pass:
- Calques from Russian grammatical structures (word-for-word RU → UA syntax)
- "благодарити" instead of "дякувати" (Russianism)
- "получити" instead of "отримати" / "одержати" (Russianism)
- "проізошло" / "проізошел" (raw Russian leaking in)
- Soviet-era bureaucratese ("отвітственний", "встрітити" — all Russianisms)

## E. Soviet-era propaganda terms used uncritically

| Forbidden (Soviet-propaganda) | Acceptable when historicized |
|---|---|
| "Буржуазний націоналізм" as a category | Only when explaining what Soviet authorities labeled people; in quotes; with context that this was Soviet smear-label |
| "Petliurivtsi" as enemy | Soldiers of UNR Army |
| "Banderivtsi" as enemy | OUN(b) members / UPA fighters |
| "Куркуль" as enemy | Wealthier peasant; Soviet authorities used as smear-label |
| "Class enemy" | Soviet-classification term; use only in quotes with framing |
| "Wrecking" / "Шкідництво" | Soviet show-trial charge; use only when describing the charge itself |
| "Trotskyism" / "Bukharinism" as wrongful identity | Show-trial pretexts; use only when describing the show trial |

## F. Source-tier policy violations

Reject the bio if:
- Soviet encyclopedia (УРЕ, БСЭ) cited as authoritative on UA figure's identity/motivation
- Russian Wikipedia cited as primary source on UA figure
- Modern Russian-state-aligned source cited (RT, Sputnik, RIA Novosti)
- Russian-language source used where a UA-language T1/T2 source exists for the same claim

Accept primary-source documents (NKVD case files, Soviet-era court records) when quoted via modern UA scholarship that contextualizes them properly.

## G. Russian-imperial place names in modern context

In body text describing modern events (post-1991), use only canonical UA names:

| Russian-imperial form | Canonical (modern context) |
|---|---|
| Kiev | Kyiv |
| Kharkov | Kharkiv |
| Lvov | Lviv |
| Ternopol | Ternopil |
| Vinnitsa | Vinnytsia |
| Odessa (BGN/PCGN-2010 spells with one s: Odesa) | Odesa |
| Nikolayev | Mykolaiv |
| Chernigov | Chernihiv |
| Belaya Tserkov | Bila Tserkva |

Historical context (1654-1917, 1917-1991) may keep the historical form in primary quotations but should clarify the canonical form on first use.

## H. Holodomor / genocide framing

Use "Holodomor" or "Голодомор", not "Soviet famine". Reference the 2006 Ukrainian Law and growing international recognition as genocide.

Avoid:
- "Famine that affected many parts of USSR" (false equivalence — Soviet authorities specifically targeted UA grain-producing regions)
- "Result of poor harvest" (it was an engineered grain confiscation)
- "Tragic but unintentional" (extensive documentary evidence shows intent)

## I. Crimea + Russia 2014– invasion

| Russocentric | Use instead |
|---|---|
| "Crimea joined Russia 2014" | "Russia illegally annexed Crimea 2014" |
| "Conflict in Donbas" | "Russian invasion of Donbas 2014" |
| "Russian-Ukrainian conflict" | "Russian war against Ukraine" / "Russian invasion of Ukraine" |
| "Pro-Russian separatists" (2014-22) | "Russia-installed proxies" / "Russia-backed fighters" |
| "Special military operation" | "Full-scale invasion 2022" |

## J. Soft-pedaling oppression

The bio's core function is to document Russian/Soviet/RF oppression of Ukrainian patriots. Reject framings that:

- Use passive voice to obscure perpetrator ("X was executed" instead of "Soviet NKVD executed X")
- Use "lost his life" where "was murdered" / "was executed" is the fact
- Hedge documented facts ("allegedly executed" when court records confirm)
- Equate Ukrainian and Russian sides as morally equivalent during invasion / occupation periods
- Use "complex" or "controversial" where the documented record is clear

---

## Automated check coverage (planned)

This checklist will eventually become enforceable via:
- VESUM Russianism detection (already exists)
- Pattern-matching against the term lists above (Phase 5 Q1)
- Cross-reference with bio-naming-canonical aliases (per #2313)
- Wiki article diff against research dossier for facts integrity

Until automation lands, this is a human-reviewer + DeepSeek-pro hermes checklist run during Phase 5 Q1 (#2336).
