> **Superseded framing note (2026-06-29):** this raw AGY review is retained as
> a review record only. Its security-service-centered language is not current guidance.
> Current Bilash guidance centers Ukrainian song canon and modern Ukrainian
> reception; the Pavlychko anecdote is optional reception context only.

FINDING:
FILE:LINE: curriculum/l2-uk-en/plans/bio/oleksandr-bilash.yaml:24
CURRENT CODE (verbatim from branch):
aliases:
- Білаш Олександр Іванович (academic-citation order)
- Oleksandr Bilash (canonical EN)
- 'Aleksandr Belash (RU/Soviet transliteration, FORBIDDEN in body text)'
- 'Aleksandr Ivanovich Belash (RU patronymic form, FORBIDDEN in body text)'
WHY WRONG:
The `aliases` array is intended for system use (search indexing and entity resolution). Including parenthetical instructional text like `(academic-citation order)` and `(FORBIDDEN in body text)` directly inside the string values means the system will register those literal strings (including the parentheses) as the aliases, corrupting the metadata.
FIX:
Remove the parenthetical instructions from the alias values. Place notes in YAML comments or remove the forbidden forms from the aliases array entirely if they shouldn't be indexed.
SEVERITY: blocker
SOURCE: none

FINDING:
FILE:LINE: curriculum/l2-uk-en/plans/bio/oleksandr-bilash.yaml:30
CURRENT CODE (verbatim from branch):
connects_to:
- bio-137-dmytro-pavlychko
- bio-39-taras-shevchenko
- bio-149-volodymyr-ivasyuk
WHY WRONG:
The `connects_to` array references fabricated slugs that include a `bio-<number>-` prefix. Checking the actual files in `curriculum/l2-uk-en/plans/bio/` reveals the files are named `dmytro-pavlychko.yaml`, `taras-shevchenko.yaml`, and `volodymyr-ivasyuk.yaml`. Linking to non-existent prefixed paths blocks the crosslink gate.
FIX:
Update the `connects_to` slugs to their correct, prefix-free values: `dmytro-pavlychko`, `taras-shevchenko`, and `volodymyr-ivasyuk`.
SEVERITY: blocker
SOURCE: none

FINDING:
FILE:LINE: curriculum/l2-uk-en/plans/bio/oleksandr-bilash.yaml:101
CURRENT CODE (verbatim from branch):
  license: VERIFY
WHY WRONG:
The `portrait_fallback` uses an image of a monument in Ukraine, and the plan leaves the license explicitly as `VERIFY`. Because Ukraine lacks Freedom of Panorama (FOP) exceptions for sculptural works, this presents an unresolved, high-risk image rights issue that blocks the source gate.
FIX:
Resolve the license verification. If the monument photo cannot be cleared due to FOP restrictions, remove the `portrait_fallback` entirely and ship text-only, as suggested in the research dossier.
SEVERITY: blocker
SOURCE: none

FINDING:
FILE:LINE: curriculum/l2-uk-en/plans/bio/oleksandr-bilash.yaml:125
CURRENT CODE (verbatim from branch):
- title: 'Дмитро Павличко про пісню «Два кольори»'
  note: Спогад співавтора про написання та підозру КДБ — первинне свідчення (VERIFY точність цитат)
  type: primary
  work: Інтерв'ю Д. Павличка
WHY WRONG:
The reference for this primary quote is vague (`Інтерв'ю Д. Павличка`) and the note explicitly delegates validation `(VERIFY точність цитат)`. There is no concrete URL or path cited for this interview, leaving it as an unsupported primary source claim that blocks the source/decolonization gate.
FIX:
Provide the specific citation or URL for this interview (e.g., the "Високий замок" article cited in the research dossier) and remove the `VERIFY` placeholder.
SEVERITY: blocker
SOURCE: none

FINDING:
FILE:LINE: wiki/figures/oleksandr-bilash.sources.yaml:34
CURRENT CODE (verbatim from branch):
  url: https://csamm.archives.gov.ua/2021/03/06/oleksandr-ivanovych-bilash-1931-2003/
WHY WRONG:
As noted in the instructions, this CSAMM link returns a 403 Forbidden error to curl. While there is no definitive evidence the source is completely dead (it may be geo-blocked or blocking automated traffic), it represents a reliability warning for future pipeline validation.
FIX:
Leave as is for now, but consider adding an archived URL (e.g., Wayback Machine) or explicitly marking it to bypass automated link checking.
SEVERITY: minor
SOURCE: none

### Verdicts

- **Base packet:** FAIL
- **Crosslink gate:** FAIL
- **Decolonization/source gate:** FAIL
