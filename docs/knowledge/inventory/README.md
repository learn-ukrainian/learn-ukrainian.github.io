# Deterministic documentation inventory

Owned by [#5536](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/5536),
under [ADR-013](../../architecture/adr/adr-013-docs-knowledge-openwiki.md) and the
[authority contract](../../architecture/docs-authority-lifecycle.md).
This is evidence tooling, not a classifier that changes source documents.

From a dispatch worktree, run:

```bash
/home/ops/learn-ukrainian/.venv/bin/python scripts/docs/docs_inventory.py
```

Stage intended documentation changes before running: the source is **Git's
index**, enumerated only with `git ls-files --stage -z`. Unstaged edits,
untracked files, ignored files, and symlink destinations are never read.
Indexed blobs work even with sparse checkout. An unresolved index fails closed.
The command never installs OpenWiki, moves documents, or edits their metadata.

## Outputs and reproducibility

Generated output goes to `audit/docs-inventory/` (or a subdirectory selected
with `--output`); keep generated receipts out of code PRs. Commit the tooling,
README, and schema only. Consumers cite `inventory_digest`, not a run date.

- `manifest.json`: conforms to [manifest.schema.json](manifest.schema.json).
  Includes path, format, byte/line counts, content SHA-256, indexed blob ID,
  HEAD path history, location observations, metadata diagnostics, lifecycle
  candidates, reference counts, and duplicate groups. No prose excerpts.
- `references.json`: version 1; `inventory_digest` and sorted unique `edges`
  with `source`, `target`, and `kind`. Kinds are `markdown_link`,
  `markdown_image`, `code_path`, `supersedes`, and `superseded_by`. Filter by
  `target` for backlinks, including code/test/config targets.
- `summary.md`: bounded aggregate counts, never a dump of external corpora.
- `digest.sha256`: the shared inventory digest plus a newline.

Canonical serialization is ASCII-escaped JSON with sorted keys, two-space
indentation, and one trailing newline. The inventory digest is SHA-256 of the
canonical object `{"manifest": manifest, "graph": graph}` **before** adding
`inventory_digest` to either object. The tracked-file digest hashes sorted
`[path, mode, blob_id]` rows for permitted regular tracked files, including
code/config targets. HEAD commit and HEAD history are recorded separately from
the indexed snapshot; staged blobs may differ from HEAD. History does not
follow renames; shallow history is explicitly flagged. No wall-clock age,
absolute checkout path, or run timestamp affects output. Identical index,
HEAD, history, and tool version produce byte-identical artifacts.

## Read boundary and evidence limits

The v1 documentation denominator is regular indexed `.md`, `.mdx`, `.rst`,
`.txt`, and `.adoc` files under `docs`, `scripts`, `site`, `tests`,
`agents_extensions`, `contracts`, `memory`, and `audit`, plus the explicit root
`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, and `README.md` instruction files.
Root instructions are classified but do not contribute graph edges.

The policy omits curriculum, wiki, data, arbitrary other root trees, deployed
harness trees, session-state, private/secret/credential directories, caches,
and generated inventory output. Exact excluded path components and read roots
are recorded in the manifest. The same boundary applies to graph targets.
This deterministic location policy is not a secret-content scanner: upstream
tracked inputs must already satisfy repository privacy rules. No arbitrary
metadata values, external URLs, unresolved target strings, or document prose
are emitted.

Markdown links (including reference definitions), image links, and exact
tracked paths in inline code are parsed using CommonMark. Fragments are
ignored, URL escapes decoded, and relative paths checked before repository-root
paths. Missing/excluded local targets contribute only an unresolved count;
external URLs are omitted. No basename guessing, network crawling, HTML/MDX
component analysis, heading validation, or code-to-document reference scan is
performed. Non-Markdown formats receive inventory facts but no link parsing.

Files over 512 KiB and non-UTF-8 files retain hashes, sizes, lines, and history,
but skip semantic analysis with a visible reason. Frontmatter is limited to
16 KiB, 2,049 tokens, and depth 32; aliases, duplicate/non-string keys, invalid
YAML and invalid field types produce stable diagnostics. Accepted lifecycle
values are `draft`, `active`, `superseded`, and `archive`. Supersession metadata
resolves only to permitted tracked targets. Leading bold authority field labels
are recorded without their potentially sensitive values. Archive location is
only a low-confidence candidate; no inferred age-based obsolescence is claimed.
Exact duplicates use content SHA-256; whitespace-normalized duplicates are
candidates only. No semantic near-duplicate claim is made.

## Cold-start baseline hook (#5543)

**Owner:** #5536 captures the pre-migration baseline; the #5535 docs-knowledge
lead coordinates it with the #5543 measurement owner. **Status: pending**;
the inventory command does not claim to measure an agent cold start.

Reserved receipt location: `audit/docs-inventory/baseline/monitor-cold-start.json`.
Use #5543's fixed question set and the real sequence: current manifest →
cached Monitor `/api/rules` → `/api/orient` → `docs/README.md`. Record the
inventory digest, Git commit, question-set identity, correctness, files read,
context bytes, calls, tokens, elapsed time, and receipt owner. Missing Monitor
or token telemetry is `unknown`, not zero and not a passing baseline. Keep
private session bodies and infrastructure details out of receipts. Publish
aggregate inventory counts and the digest to #5535; do not commit generated
status/telemetry artifacts. This hook is not proof that the measurement ran.
