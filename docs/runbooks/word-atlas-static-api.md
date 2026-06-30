# Word Atlas Static API Contract

The learner site is GitHub Pages/static-first. Atlas runtime data is exposed
as static JSON, not as a live backend service.

## Canonical Endpoints

- `/api/lexicon/status.json` — status counts across Atlas search/browse,
  manifest hydration, Daily Word, Practice, cloze, and source-inventory
  admission.
- `/api/lexicon/search-index.json` — compact typeahead/search rows.
- `/api/lexicon/daily-pool.json` — Daily Word pool.
- `/api/lexicon/practice-index.{level}.json` — per-level Practice index.
- `/api/lexicon/practice-lexemes.{level}.json` — per-level Practice lexeme deck.
- `/api/lexicon/practice-cloze.{level}.json` — per-level reviewed cloze deck.

The status payload also points to existing static browse assets:

- `/lexicon/browse/{letter}.json`

## Contract Checks

Consumers should treat `status: "ok"` as the normal state. `warning` means at
least one public surface drifted, search/browse counts disagree, practice deck
versions split, Daily Word became empty, or the hydrated manifest no longer
matches the public Atlas count.

`sourceInventory` counts only become non-null when the build has a hydrated
release manifest. Missing `surface_admission` remains false; source-inventory
growth is Atlas browse/search only until a reviewed decision admits Daily Word,
Practice, or cloze.

## Deployment Rule

Do not add FastAPI routes for public Atlas learner data unless the deployment
target changes away from GitHub Pages or the route is explicitly local/admin
only. Public learner data must stay available as static JSON.
