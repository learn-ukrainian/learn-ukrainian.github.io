# Word Atlas Static API Contract

The learner site is GitHub Pages/static-first. Atlas runtime data is exposed as
static JSON, not a live backend service.

## Canonical Endpoints

- `/api/lexicon/status.json` — status and counts across Atlas search/browse,
  manifest hydration, Daily Word, Practice, cloze, and source-inventory
  admission.
- `/api/lexicon/search-index.json` — compact typeahead/search rows.
- `/api/lexicon/daily-pool.json` — Daily Word pool.

The status payload also points at the existing static practice and browse
assets:

- `/lexicon/browse/{letter}.json`
- `/lexicon/practice-index.{level}.json`
- `/lexicon/practice-lexemes.{level}.json`
- `/lexicon/practice-cloze.{level}.json`

## Contract Checks

Consumers should treat `status: "ok"` as the normal state. A warning means at
least one public surface drifted, such as search and browse counts disagreeing,
practice deck versions splitting, Daily Word becoming empty, or the hydrated
manifest no longer matching the public Atlas count.

`sourceInventory` counts only become non-null when the build has hydrated the
release manifest. Missing `surface_admission` remains false; source-inventory
growth is Atlas browse/search only until a reviewed decision admits Daily Word,
Practice, or cloze.

## Deployment Rule

Do not add FastAPI routes for public Atlas learner data unless the deployment
target changes away from GitHub Pages or the route is explicitly local/admin
only. Public learner data must stay available as static JSON.
