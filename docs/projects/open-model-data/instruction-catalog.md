# E10 instruction catalog — draft 0.3.0

Issue #9611; parent #6321. Author: GPT-6.1 Sol, Codex.
This is a **draft**, with `training_eligible: false`. Round 3 addresses the
Opus and Flash findings on `e3eed1e5989b7683c16dffe8fbc8b819effaa3ff`;
it does not certify PA6. The driver adopts the stricter numerical bounds
**top1 ≤ 0.15, top5 ≤ 0.60**; the round-2 brief's 0.65 is superseded.

[Catalog](../../../registry/projects/open_model_data/instruction_catalog.yaml) ·
[Versioned structural schema](../../../registry/projects/open_model_data/instruction_catalog.schema.json) ·
[Committed checks](../../../tests/projects/open_model_data/test_instruction_catalog.py) · [Plan](PLAN.md)

## Scope and counts

Only `components.*.instructions[].template` is project-written training text.
Control metadata and evidence never become instructions, answers or reasoning.
No answer text, explanation or worked solution is authored here.

| Component | Lines | Operations and source units |
| --- | ---: | --- |
| C1 | 12 | Sentence correction including unchanged no-edit pairs. |
| C2 | 12 | All agreed variants; fixed source-header serialization and visible sense. |
| C3 | 24 | 12 synonym and 12 antonym lines; source-readable sense labels. |
| C4 | 12 | Dictionary definition **and citation from the same entry**. |
| C5 | 12 | Full Правопис § containing its printed example. |
| C6 | 24 | 12 calque-only sentence lines and 12 signed book-replacement lines. |
| C7 | 12 | Modern-attested side of an admitted opt-in contrast pair. |
| C8 | 12 | Normative/admissible transcription and the author's quoted verdict. |
| C9 | 12 | Complete text under an authenticated printed textbook heading. |
| **Total** | **132** | **9 components, 11 operations, 12 lines per operation.** |

Twelve distinct starts per operation give balanced top1 = 1/12 (8.33%) and
top5 = 5/12 (41.67%). Dropping two disputed lines leaves ten starts:
0.10/0.50. Both retain slack under the proposed 0.15/0.60 prefix bounds.
Counts establish scheduling capacity, not semantic variety or model quality.

## Binding and interpolation rules

Slots are binding roles, never guessed physical database columns. E4 must
authenticate source adapters and exact row/field/span locators. Interpolation
is single-pass and verbatim: no inflection, paraphrase, truncation, added stress,
replacement or recursive expansion. The sole serialization exception is the
fixed C2 header/target JSON specified below (PLAN P1(c)); no free-form joining.
Braces in source values remain literal.
Missing, ambiguous or inapplicable fields withhold the record. E4/E5 supplies
source context and authenticated fields; C2 fixes its lossless header and
variant serialization below, rather than guessing a single printed label.

Sentences, printed examples and phonetic contexts follow a colon without outer
quotes or added terminal punctuation. A source sentence's own punctuation and
internal quotes remain intact. Other quoted slots withhold values containing
guillemets, preventing nested same-form quotes without transforming the source.
All `{sense}` slots are final fields after `Значення:`, without outer quotes
or added terminal punctuation. Parentheses and terminal `. , ; :` stay
verbatim; there is no `«(…)»` wrapper or doubled full stop. This policy is
explicit in `interpolation.quoted_slot_policy` and enforced in the C2/C3
template patterns, with six source-value fixtures and quotation mutations.

- **C1:** same-document/annotator aligned pairs; all annotations and both
  UA-GEC layers stay together. Unchanged no-edit pairs remain eligible and
  target the unchanged sentence. Every line allows preservation, without
  presupposing an error or asking for an explanation.
- **C2:** lemma, fixed source-header serialization and verbatim `sense_gloss`
  are model-visible in every line. Numeric homonym identifiers and code tags
  stay in lossless metadata, never substitutes for printable cells. Where
  homonym forms differ, withhold missing or non-discriminating source senses.
  One target contains all agreed variants. P3 exclusions and VESUM/ULIF
  tuple agreement still bind; incomplete agreement withholds the whole record.
- **C3:** the group must belong to the selected headword sense. Withhold if no
  source-readable sense label exists; a numeric sense ID cannot become a gloss.
  Both .03 lines use `до слова`, not `для слова`.
- **C4:** **citation stays in the target**, together with the definition from
  that same dictionary entry. Every instruction requests both explicitly.
  Never invent an example; exclude ruler-overlapping citations.
- **C5:** E3b stores complete §§ with locators, not separate sub-points.
  Accordingly every line requests the full **параграф Правопису** containing
  its own printed example. The § locator is mandatory context, especially
  when an example appears in multiple §§. No outside-case rule selection.
- **C6:** a sentence×annotator unit must have at least one edit and **only
  F/Calque edits**. Mixed units belong to C1; no-edit units cannot enter C6.
  The full aligned human correction is then a calque-only target. Book pairs
  require both forms printed in the same cited passage and individual Sol
  and Opus sign-off. Every book line admits one or several replacements,
  using `заміну (заміни)` or neutral `замінити` wording. `автор` refers to
  authenticated author context; no
  dangling book reference or invented sentence bridge remains.
- **C7:** no interpolation slots. The admitted #8982 pair is mandatory context,
  with modern-source and Soviet-context roles. SUM-11 never supplies the norm;
  unadjudicated pairs, the default split and pretraining remain excluded.
- **C8:** printed word and phonetic context require transcription, supporting
  paragraph span, same-paragraph verdict, rule/page and ULIF stress cross-check.
  All lines request normative/admissible transcription **and** the author's
  assessment, with author identity in context. Wording varies throughout;
  no repeated second sentence or dangling paragraph reference remains.
  Non-norm-only paragraphs, ambiguous verdicts, mismatches and illegible
  notation are withheld. A non-norm reading is only on the rejected side.
- **C9:** `section_title` is a heading **printed in textbook text**, extracted
  verbatim with position by #8341. It is keyed by verbatim book title, grade
  or level, unit identity and page. Lines ask for text **під заголовком**:
  this fits a theme, § or chapter without miscalling every unit `розділ`.
  Refuse ingester labels (`Сторінка N`, `Reference N`, `Entry N`,
  `Private lesson …`) and **all non-textbook files**. Existing section labels
  alone prove no eligible heading. Until #8341 provides printed-heading
  evidence, withhold records. Targets are complete verbatim headed units;
  no summaries, unkeyed exercises, contents pages or OCR-damaged text.
  The printed-question/printed-answer route uses source text directly.

The Draft 2020-12 schema uses typed version/plan/status/metric metadata, rather
than constants pinning one draft. It can validate an approved version's shape;
it cannot grant approval or training eligibility. Drafts must remain ineligible.
Component/operation and source-role constraints remain closed. Every declared
slot must occur in its template (schema lookaheads and committed mutation tests);
the committed test also requires placeholder order to match `slots` exactly.

## C2 fixed header cells and variant target

`c2-header-cells.v1` is UTF-8 JSON, emitted with
`json.dumps(value, ensure_ascii=False, separators=(",", ":"))`. Key order is
exactly `section_headers`, `row_header`, `column_headers`. All values are
**verbatim source strings**, never code expansions:

- `section_headers`: zero, one or two cells, parent tense/mood followed by
  the active verb-form subsection, in source order. An absent level contributes
  no array element; changing the parent clears the prior subsection.
- `row_header`: the source row-label cell, or the empty string if absent.
- `column_headers`: all active stacked column-header cells above the selected
  form cell, in source order, or an empty array if absent.

At least one header string must be nonempty. Read the same physical cells as
`scripts/lexicon/runner/ulif_dictua_parse.py::_paradigm_form_rows`: resolve
rowspan/colspan on `payload_json.raw_html`, retain parent/subsection headers,
row labels and stacked column headers. The parser's header recognition selects
cells; it must not rewrite their text into a synthetic grammatical label.
Cross-check the printed strings against `payload_json.rows`; preserve section
id, table coordinates and header-cell span locators in metadata. A missing,
unknown, unmapped or conflicting header association withholds the record.
No string concatenation, translated labels or arbitrary joining is permitted.
JSON escaping is reversible structural serialization, not source rewriting.

The `{lemma}` slot copies `ulif_dictua_entries.canonical_headword` verbatim;
E4 authenticates its link to the P3 lemma without rewriting the visible
source headword. The input also contains `ulif_dictua_entries.sense_gloss`
verbatim after the last colon. Empty senses are permitted only if homonym forms do not differ
for the same headword and grammatical slot. Compare **complete ordered variant
targets**, not one selected form: if different targets remain possible for the
same visible lemma/header/sense, withhold. A missing gloss in a differing
homonym group or one gloss shared by conflicting targets cannot discriminate
it. Source sense labels, not `homonym_index`, must resolve that ambiguity.

The target is a single JSON array of all agreed `ulif_forms.form_stressed`
values for that entry/slot, ordered by `(variant_order, id)`; retain duplicates
and every variant's locator/identity. Every variant must satisfy P3 agreement
and exclusions, otherwise withhold the **whole** record. Never silently pick
a preferred variant. This uses the same fixed JSON encoding as the header slot.
The schema's `c2HeaderCells` and `c2SourceRecord` definitions supply admission
**shape** fixtures, not proof of authenticity, completeness, or cross-record
uniqueness; those remain E4/E5 gates.

## C2 source-field eligibility census

Read-only snapshot on 2026-10-03; reproduction uses the task-prescribed project
interpreter and canonical ULIF store with SQLite URI `mode=ro`. The query below
starts one read transaction and writes only connection-local TEMP tables.
This is a **conservative lower bound on ULIF field eligibility**, measured in
entry×grammatical-slot records, not exported training records or completed
VESUM agreement. It covers only full three-column noun tables with all seven
printed case rows; verb, adjective, invariable and other table shapes are not
counted. There is no promise that every counted record passes E4 authentication,
P3 VESUM/sense agreement, held-out exclusions or E5 export admission.

Baseline queries and raw outputs:

```sql
SELECT count(*) FROM ulif_forms; -- 4742272
SELECT count(*) FROM ulif_dictua_entries
WHERE homonym_checked=1 AND status='ok'; -- 262735
SELECT count(DISTINCT entry_id) FROM ulif_forms
WHERE unmapped_labels!='[]'; -- 81984
```

The field rule leaves **644,515 records across 93,299 entries**, containing
673,969 source variant rows, eligible in this slice. This includes 29,432
multi-variant records and 13,924 records from differing-homonym groups with
discriminating visible glosses. It withholds 15,653 candidates for sense
ambiguity. Thus the source-field rule does not reduce C2 to near zero; final
training-admitted counts remain E4/E5's responsibility.

Set `LU_SOURCES_DB` to the canonical store's absolute path and run this exact
query/selection with `"$LU_PROJECT_PYTHON"` from the assigned worktree:

```python
import json, os, sqlite3
c=sqlite3.connect('file:'+os.environ['LU_SOURCES_DB']+'?mode=ro',uri=True)
c.execute('BEGIN')
q='''CREATE TEMP TABLE form_sets AS
SELECT e.id entry_id,e.normalized_query headword,e.sense_gloss,f.grammatical_tags,
       group_concat(f.form_stressed,char(31)) forms,count(*) variants,
       max(f.marked_asterisk) asterisk,max(f.preposition!='') bound
FROM (SELECT * FROM ulif_forms WHERE is_lemma=0 ORDER BY entry_id,grammatical_tags,variant_order,id) f
JOIN ulif_dictua_entries e ON e.id=f.entry_id
WHERE e.status='ok' AND e.homonym_checked=1
GROUP BY e.id,f.grammatical_tags'''
c.execute(q)
c.execute('CREATE INDEX temp.set_key ON form_sets(headword,grammatical_tags)')
c.execute('''CREATE TEMP TABLE conflicts AS SELECT headword,grammatical_tags
FROM form_sets GROUP BY headword,grammatical_tags HAVING count(DISTINCT forms)>1''')
c.execute('CREATE INDEX temp.conflict_key ON conflicts(headword,grammatical_tags)')
q2='''SELECT e.id,s.payload_json FROM ulif_dictua_sections s
JOIN ulif_dictua_entries e ON e.id=s.entry_id
WHERE s.kind='paradigm' AND e.status='ok' AND e.homonym_checked=1
AND json_extract(s.payload_json,'$.rows[0]')='["відмінок","однина","множина"]'
AND json_array_length(s.payload_json,'$.rows')=8
AND NOT EXISTS (SELECT 1 FROM json_each(s.payload_json,'$.rows') r WHERE json_array_length(r.value)!=3)
AND NOT EXISTS (SELECT 1 FROM ulif_forms f WHERE f.entry_id=e.id AND f.unmapped_labels!='[]')
AND NOT EXISTS (SELECT 1 FROM ulif_forms_failures x WHERE x.entry_id=e.id)'''
c.execute('CREATE TEMP TABLE noun_entries(entry_id INTEGER PRIMARY KEY)')
cases=['називний','родовий','давальний','знахідний','орудний','місцевий','кличний']
for entry,payload in c.execute(q2).fetchall():
 rows=json.loads(payload)['rows']
 if [r[0] for r in rows[1:]]==cases:
  c.execute('INSERT OR IGNORE INTO noun_entries VALUES(?)',(entry,))
q3='''CREATE TEMP TABLE candidates AS SELECT a.* FROM form_sets a JOIN noun_entries n USING(entry_id)
WHERE a.asterisk=0 AND a.bound=0
AND json_array_length(a.grammatical_tags)=2
AND json_extract(a.grammatical_tags,'$[0]') IN ('v_naz','v_rod','v_dav','v_zna','v_oru','v_mis','v_kly')
AND json_extract(a.grammatical_tags,'$[1]') IN ('s','p')'''
c.execute(q3)
q4='''CREATE TEMP TABLE eligible AS SELECT a.* FROM candidates a
WHERE NOT EXISTS(SELECT 1 FROM conflicts k WHERE k.headword=a.headword AND k.grammatical_tags=a.grammatical_tags)
OR (trim(a.sense_gloss)!='' AND NOT EXISTS (
 SELECT 1 FROM form_sets b WHERE b.headword=a.headword AND b.grammatical_tags=a.grammatical_tags
 AND (trim(b.sense_gloss)='' OR (b.sense_gloss=a.sense_gloss AND b.forms!=a.forms))))'''
c.execute(q4)
for name,q in {
 'complete_mapped_noun_entries':'SELECT count(*) FROM noun_entries',
 'noun_entry_tag_candidates':'SELECT count(*) FROM candidates',
 'noun_entry_tag_field_eligible':'SELECT count(*) FROM eligible',
 'noun_entries_field_eligible':'SELECT count(DISTINCT entry_id) FROM eligible',
 'noun_variant_rows_field_eligible':'SELECT sum(variants) FROM eligible',
 'noun_multivariant_records':'SELECT count(*) FROM eligible WHERE variants>1',
 'noun_sense_withheld':'SELECT (SELECT count(*) FROM candidates)-(SELECT count(*) FROM eligible)',
 'noun_differing_homonym_records':'SELECT count(*) FROM eligible a JOIN conflicts k USING(headword,grammatical_tags)',
}.items(): print(name,c.execute(q).fetchone()[0],flush=True)
```

Raw result:

```text
complete_mapped_noun_entries 95200
noun_entry_tag_candidates 660168
noun_entry_tag_field_eligible 644515
noun_entries_field_eligible 93299
noun_variant_rows_field_eligible 673969
noun_multivariant_records 29432
noun_sense_withheld 15653
noun_differing_homonym_records 13924
```

The census excludes entire entries with any unmapped labels or recorded forms
failure and entire slot groups with any asterisk/preposition-bound variant.
It counts only non-lemma form rows under authenticated-entry status. Missing
source senses in any differing homonym group conservatively withhold that
group; equal glosses with different complete targets are also withheld. The
header locator/byte proof is still E4's gate, not supplied by these SQL counts.

## Proposed concentration measures

The driver adopts **0.15/0.60** for prefix, ID and whole-template bounds in
this round. Metric protocol/version and export enforcement remain draft.
The accountable driver freezes catalog bytes/hash,
metric version and thresholds after non-author reviews and before E12. Prior
art: `check_2_form_letters` in
`scripts/projects/open_model_data/audit_dataset_acceptance.py` measures
whole-text frequency. This draft does not change it or the production checker.

1. Before counting, validate catalog version/hash and ID; re-render authenticated
   fields byte for byte. Unknown IDs, changed literals, missing spans/locators,
   multiple catalog IDs or extra authored text fail the relationship gate.
2. Count the matched **template**, with every placeholder replaced by atomic
   `SLOT`. Source values, slot names, context, questions, targets, citations and
   reasoning cannot supply diversity. Original printed questions have a separate
   `source_question` denominator.
3. For comparison only: NFC, Unicode casefold and U+0027 apostrophe to U+2019.
   Tokens are Unicode letter runs with an internal apostrophe, including `slot`
   as one token. Punctuation separates tokens. No stemming, model tokenizer or
   language-model judgment; source/export bytes stay untouched.
4. For each **(component, operation, exported split)**, N is the actual record
   count; each record contributes once, without deduplication. C7 is separate
   and opt-in. Whole-split totals are diagnostic and cannot rescue a bucket.
   N = 0 is missing coverage; N < 10 is insufficient evidence, never PASS.
5. `instruction-prefix.v1-draft`: independently count the first **one** and
   **four** tokens, using the full tuple if shorter. With descending counts n_i,
   `top1 = max(n_i)/N`, `top5 = sum(five largest n_i)/N` (all if fewer than five).
   Proposed bounds: **top1 ≤ 0.15, top5 ≤ 0.60**, at both lengths and on ID
   frequencies. Compare exact ratios, never rounded allowances.
6. `instruction-repetition.v1-draft`, using the same N and tokenization:
   - **Whole template:** full-token tuple frequencies, top1 ≤ 0.15 and top5 ≤ 0.60.
   - **Suffix:** last **eight** tokens (full tuple if shorter), top1 ≤ **0.60**.
     Report distinct suffixes, top1 and diagnostic top5.
   - **Whole-template n-grams:** all contiguous **eight-token** grams anywhere
     in a template (one full-tuple gram if shorter). Count each distinct gram
     **once per record**, even if repeated inside it. Maximum record prevalence
     `max_gram(records containing gram)/N` ≤ **0.60**. Denominator is records,
     never gram positions. Report the leading grams and their shares.
   These catch the old C8 repeated second sentence (prevalence 1.0), even if
   moved into the middle. Eight tokens capture a shared sentence-length span
   while allowing short binding vocabulary. This does not prove semantic variety.
7. Report N, distinct prefixes/templates/suffixes, their shares and ID shares.
   Source-unit/fingerprint/locator diversity is independent with its own
   denominator. Distinct sentences under one instruction still fail here.
   Report instruction-origin counts against the frozen component manifest.

With 12 balanced lines, prefixes/IDs/whole templates give 0.0833/0.4167.
After any two starts are dropped, 0.10/0.50 stays below 0.15/0.60. The n-gram
and suffix 0.60 proposal refuses a common long span in a majority exceeding
three fifths, with slack for necessary repeated relational language. In the
current balanced catalog, maximal n-gram/suffix prevalence is at most 2/12.
These are anti-concentration limits, not confidence intervals or held-out proof.

Check feasibility against admitted records and fields before building, without
reading the sealed final ruler. Schedule semantically eligible instructions
under the frozen version. Never rewrite, duplicate or rebind sources to pass.
Infeasible integer counts or fewer than ten eligible lines withhold the bucket
and return it to the driver; dropping a disputed line never licenses relaxation.

## Round 3 concentration diagnostics

Recomputed with `tokens`, `shares` and `repetition` in the committed test,
loaded with the task-prescribed interpreter via `importlib.util.spec_from_file_location`.
For **each of the 11 operations**, N=12: one-token prefix, four-token prefix,
whole template and ID frequencies are all **top1=1/12, top5=5/12**
(0.083333…/0.416666…). They remain below **0.15/0.60**. After dropping the
last two lines, the committed arithmetic test requires **0.10/0.50**.

The following are maximum **record prevalence**, with grams counted once per
record. The 4-, 5- and 6-gram columns are **diagnostics only**, never gates;
necessary binding vocabulary can concentrate. Eight-gram and suffix bounds
remain 0.60. No source value or slot name contributes token diversity.

| Component.operation | 4-gram | 5-gram | 6-gram | 8-gram | 8-token suffix top1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| C1.sentence_correction | 3/12 | 2/12 | 1/12 | 1/12 | 1/12 |
| C2.agreed_form | 4/12 | 4/12 | 4/12 | 1/12 | 1/12 |
| C3.synonyms | 9/12 | 5/12 | 5/12 | 1/12 | 1/12 |
| C3.antonyms | 9/12 | 5/12 | 5/12 | 1/12 | 1/12 |
| C4.idiom_definition | 4/12 | 4/12 | 1/12 | 1/12 | 1/12 |
| C5.printed_spelling_rule | 3/12 | 1/12 | 1/12 | 1/12 | 1/12 |
| C6.calque_correction | 2/12 | 1/12 | 1/12 | 1/12 | 1/12 |
| C6.book_calque_replacement | 7/12 | 6/12 | 6/12 | 1/12 | 1/12 |
| C7.modern_norm_selection | 5/12 | 3/12 | 3/12 | 1/12 | 1/12 |
| C8.supported_pronunciation | 9/12 | 8/12 | 8/12 | 2/12 | 1/12 |
| C9.verbatim_section | 12/12 | 8/12 | 5/12 | 2/12 | 2/12 |

Reproduction (inside the assigned worktree):

```python
import importlib.util
spec = importlib.util.spec_from_file_location(
    "catalog_test", "tests/projects/open_model_data/test_instruction_catalog.py"
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
for component, entry in m.CATALOG["components"].items():
    for operation in sorted({line["operation"] for line in entry["instructions"]}):
        seqs = [m.tokens(line["template"]) for line in entry["instructions"]
                if line["operation"] == operation]
        print(component, operation,
              "prefix1", m.shares([seq[:1] for seq in seqs]),
              "prefix4", m.shares([seq[:4] for seq in seqs]),
              "whole", m.shares(seqs),
              "suffix8/ngram8", m.repetition(seqs),
              "grams4/5/6", [m.repetition(seqs, n)[1] for n in (4, 5, 6)])
```

## Committed checks and remaining production proof

`tests/projects/open_model_data/test_instruction_catalog.py` checks schema/plan hash, counts/IDs,
every declared slot, a missing-slot mutation for each applicable slot,
versionable approval metadata, closed roles, sentence interpolation and
concentration arithmetic. Negative fixtures cover:

| Fixture | Expected arithmetic/contract result |
| --- | --- |
| Single repeated template | Prefix/template/suffix/n-gram shares 1.0: FAIL. |
| Twelve balanced lines, then two dropped | Prefix/ID/template limits retain slack. |
| Distinct IDs with one first token | Prefix top1 = 1.0: FAIL. |
| Balanced prefixes with old C8 suffix | Suffix and n-gram prevalence 1.0: FAIL. |
| Old C8 sentence moved into the middle | Whole-template n-gram prevalence 1.0: FAIL. |
| Same gram repeated many times inside a record | Count that record once. |
| Short templates | Full tuple retained, never omitted. |
| Missing declared slot or invented role/answer | Schema refusal. |

**These are local contract/arithmetic fixtures, not the E5-backed exported-record
checker or independent held-out proof.** AC4 remains pending E5 integration.
D4 remains the evaluation steward's independent sealed proof; this author did
not inspect the sealed ruler. Real source-field applicability and relationship
verification remain E4/E5 responsibilities.

## Historical round 2 finding disposition

| Review finding | Change |
| --- | --- |
| Opus 1: unavailable C9 slot, identity and wrong chapter term | Printed heading/position via #8341; title + grade slots; label/non-textbook exclusions; text-under-heading wording. |
| Opus 2: C2 identifiers displayed | Homonym/tags only in context; printable grammatical source label or withhold. |
| Opus 3: C6 mixed edits | Calque-only sentence×annotator binding and exclusion; mixed units to C1. |
| Opus 4: C1 no-edit units | Remain eligible; all instructions allow preserving correct sentences. |
| Opus 5: quotation punctuation | Sentence/example/context after colon; quoted slots cannot nest guillemets. |
| Opus 6: C4 omitted citation request | Definition plus same-entry citation explicitly requested in every line; both stay in target. |
| Opus 7: concentration/slack | 12 lines/operation; 0.15/0.60 proposal; suffix and whole-template 8-gram prevalence. |
| Opus 8 + Flash C3 .03 fixes | `до слова` in both synonym/antonym .03 lines. |
| Opus 9: dangling references | Author identified in context; C6/C8 refer to author, without unnamed book/paragraph. |
| Opus 10: C5 wrong unit | Full § requested, matching E3b storage; no sub-point selection. |
| Opus 11: evidence/schema/test nits | Official offline Правопис proof; mandatory slots + committed mutations; typed versionable metadata. |
| Flash C2.agreed_form.03 | `форму слова`; no `для` and no visible homonym ID. |
| Flash C5.printed_spelling_rule.01 | Full paragraph containing its printed example; no `для` or unresolved pronoun. |

## Historical round 2 Sources evidence

Tool checkpoint: `2026-10-03T19:19:01Z` (`date -u`). Sources batch started `2026-10-03T19:12:33Z`.
Catalog SHA-256: `b0a8f16e6ccedff3f4222882ec1993d6fa135d711d65d67d95a7dc64af0fcbb7`.

The connected Sources instance returned `No pravopys section found for: '164'`
and the older mirror for §23. A transient **stdio Sources MCP session**, launched
from this worktree with the prescribed project interpreter and the canonical
`LU_SOURCES_DB` override, supplied the evidence below. No shared service was
restarted. Calls used `ClientSession.call_tool`, not replacement lookup logic.
All source reads were read-only; request diagnostics stayed outside the worktree.

Form attestation proves morphology, not sentence naturalness. Russian-shadow
checks are suspicion detectors, never a calque verdict. Both Антоненко surfaces
were queried for every changed/new line; empty retrieval is not approval and
keyword hits do not attest the whole sentence. The two source-search surfaces
are style evidence; Правопис supplies spelling/punctuation authority. Independent
non-author language/semantic review of this new head is still required.

There are 110 changed/new templates; 22 prior templates retain their wording.
Each per-line call strips placeholders, lowercases authored words for VESUM,
and verifies the distinct literal words with `verify_words`. The style/book
query is the space-joined Cyrillic word runs from the literal template in its
original case. Both searches use `limit=1`; `search_text` also uses
`source_file='antonenko-davydovych-yak-my-hovorymo'`. Below are exact returned
`Found` summaries and full search status lines, with returned book chunk IDs.
These are capped retrieval counts, never total matches across the book.

### Official offline Правопис

Call: `query_pravopys(topic='164')`. Returned `source_id: pravopys_2019_official`.

```text
**Український правопис (2019), § 164. Лапки (« », “ ”, „ “, рідше „ ”)**
**Locator**: Український правопис. Київ: Наукова думка, 2019, § 164, с. 246–248
**Source**: official authorized edition (Наукова думка, 2019), stored offline in sources.db — https://www.ulif.org.ua/system/files/pravopus-new.pdf (sha256 0d2fd75a2e9b…, retrieved 2026-10-03T15:53:24Z)
```

Exact punctuation note from this response:

```text
Примітка 1. Такі розділові знаки, як крапка, кома, крапка з комою,
двокрапка й тире, ніколи не ставимо перед закритими лапками, а
тільки після них.
```

Exact nested-quote guidance:

```text
доцільно використовувати лапки різної форми — зовнішні і
внутрішні.
```

Call: `query_pravopys(topic='23')`. Returned `source_id: pravopys_2019_official`.

```text
**Український правопис (2019), § 23. Уживання прийменників У, В і початкових У-, В-**
**Locator**: Український правопис. Київ: Наукова думка, 2019, § 23, с. 25–28
**Source**: official authorized edition (Наукова думка, 2019), stored offline in sources.db — https://www.ulif.org.ua/system/files/pravopus-new.pdf (sha256 0d2fd75a2e9b…, retrieved 2026-10-03T15:53:24Z)
```

Call: `query_pravopys(topic='155')`. Returned `source_id: pravopys_2019_official`.

```text
**Український правопис (2019), § 155. Крапка (.)**
**Locator**: Український правопис. Київ: Наукова думка, 2019, § 155, с. 197–199
**Source**: official authorized edition (Наукова думка, 2019), stored offline in sources.db — https://www.ulif.org.ua/system/files/pravopus-new.pdf (sha256 0d2fd75a2e9b…, retrieved 2026-10-03T15:53:24Z)
```

Call: `query_pravopys(topic='160')`. Returned `source_id: pravopys_2019_official`.

```text
**Український правопис (2019), § 160. Двокрапка (:)**
**Locator**: Український правопис. Київ: Наукова думка, 2019, § 160, с. 228–230
**Source**: official authorized edition (Наукова думка, 2019), stored offline in sources.db — https://www.ulif.org.ua/system/files/pravopus-new.pdf (sha256 0d2fd75a2e9b…, retrieved 2026-10-03T15:53:24Z)
```

E3b stores §§ with paragraph locators. The queried official §23 spans pages
25–28; C5 therefore asks for the complete paragraph, not one sub-point.
The official note supersedes the old draft's mirror-only evidence.

### Forms and Russian shadow

Calls: `check_text(items=<110 literal templates>, checks=['vesum',
'russian_shadow'], max_findings=200)`. Exact returned summary/problemlists:
Stress and UA-GEC checks were not requested; their zero counters below do not
establish verification of those facets.

```json
{
  "summary": {
    "tokens": 920,
    "unique_forms": 204,
    "problems_per_check": {
      "vesum": 0,
      "stress": 0,
      "russian_shadow": 0,
      "ua_gec": 0
    },
    "suspicions_count": 0,
    "uncut_count": 0,
    "truncated": false
  },
  "problems": [],
  "suspicions": []
}
```

Imperative disambiguation: `verify_words(pos_filter="verb", words=<the 22 forms below>)`. Exact response:

```text
25 analyses (25 distinct lemmas)

Batch verification: 22 words

Found: 22/22

- **перевір** — FOUND (1 analysis (1 distinct lemma)): перевірити(verb)
- **подай** — FOUND (1 analysis (1 distinct lemma)): подати(verb)
- **запиши** — FOUND (1 analysis (1 distinct lemma)): записати(verb)
- **відредагуй** — FOUND (1 analysis (1 distinct lemma)): відредагувати(verb)
- **усунь** — FOUND (1 analysis (1 distinct lemma)): усунути(verb)
- **наведи** — FOUND (1 analysis (1 distinct lemma)): навести(verb)
- **збережи** — FOUND (1 analysis (1 distinct lemma)): зберегти(verb)
- **виправ** — FOUND (2 analyses (2 distinct lemmas)): виправити(verb), випрати(verb)
- **залиш** — FOUND (1 analysis (1 distinct lemma)): залишити(verb)
- **добери** — FOUND (2 analyses (2 distinct lemmas)): дібрати(verb), добрати(verb)
- **вкажи** — FOUND (1 analysis (1 distinct lemma)): вказати(verb)
- **утвори** — FOUND (1 analysis (1 distinct lemma)): утворити(verb)
- **постав** — FOUND (2 analyses (2 distinct lemmas)): поставити(verb), постати(verb)
- **назви** — FOUND (1 analysis (1 distinct lemma)): назвати(verb)
- **відтвори** — FOUND (1 analysis (1 distinct lemma)): відтворити(verb)
- **перелічи** — FOUND (1 analysis (1 distinct lemma)): перелічити(verb)
- **процитуй** — FOUND (1 analysis (1 distinct lemma)): процитувати(verb)
- **додай** — FOUND (1 analysis (1 distinct lemma)): додати(verb)
- **заміни** — FOUND (1 analysis (1 distinct lemma)): замінити(verb)
- **позбудься** — FOUND (1 analysis (1 distinct lemma)): позбутися(verb)
- **обери** — FOUND (1 analysis (1 distinct lemma)): обрати(verb)
- **випиши** — FOUND (1 analysis (1 distinct lemma)): виписати(verb)
```

### Per-line source calls

| ID | verify_words | search_style_guide | search_text; returned chunk |
| --- | --- | --- | --- |
| C1.sentence_correction.01 | `Found: 8/8` | `No results in Антоненко-Давидович for: "Перевір речення і виправ помилки якщо вони є"` | `Found 1 results for: "Перевір речення і виправ помилки якщо вони є"`; `antonenko-davydovych-yak-my-hovorymo_p144` |
| C1.sentence_correction.02 | `Found: 8/8` | `No results in Антоненко-Давидович for: "Подай речення після перевірки виправ лише наявні помилки"` | `Found 1 results for: "Подай речення після перевірки виправ лише наявні помилки"`; `antonenko-davydovych-yak-my-hovorymo_p169` |
| C1.sentence_correction.03 | `Found: 7/7` | `No results in Антоненко-Давидович for: "Запиши речення виправивши помилки якщо вони є"` | `Found 1 results for: "Запиши речення виправивши помилки якщо вони є"`; `antonenko-davydovych-yak-my-hovorymo_p144` |
| C1.sentence_correction.04 | `Found: 9/9` | `No results in Антоненко-Давидович for: "Відредагуй речення якщо воно потребує виправлень інакше збережи його"` | `Found 1 results for: "Відредагуй речення якщо воно потребує виправлень інакше збережи його"`; `antonenko-davydovych-yak-my-hovorymo_p158` |
| C1.sentence_correction.05 | `Found: 8/8` | `No results in Антоненко-Давидович for: "Усунь помилки якщо вони є і запиши речення"` | `Found 1 results for: "Усунь помилки якщо вони є і запиши речення"`; `antonenko-davydovych-yak-my-hovorymo_p144` |
| C1.sentence_correction.06 | `Found: 9/9` | `No results in Антоненко-Давидович for: "Наведи речення після перевірки зберігши його якщо помилок немає"` | `Found 1 results for: "Наведи речення після перевірки зберігши його якщо помилок немає"`; `antonenko-davydovych-yak-my-hovorymo_p117` |
| C1.sentence_correction.07 | `Found: 8/8` | `No results in Антоненко-Давидович for: "Речення перевір і запиши за потреби виправ помилки"` | `Found 1 results for: "Речення перевір і запиши за потреби виправ помилки"`; `antonenko-davydovych-yak-my-hovorymo_p144` |
| C1.sentence_correction.08 | `Found: 10/10` | `No results in Антоненко-Давидович for: "Як слід записати це речення Якщо помилок немає збережи його"` | `Found 1 results for: "Як слід записати це речення Якщо помилок немає збережи його"`; `antonenko-davydovych-yak-my-hovorymo_p117` |
| C1.sentence_correction.09 | `Found: 9/9` | `No results in Антоненко-Давидович for: "Збережи речення якщо воно правильне якщо є помилки виправ їх"` | `Found 1 results for: "Збережи речення якщо воно правильне якщо є помилки виправ їх"`; `antonenko-davydovych-yak-my-hovorymo_p100` |
| C1.sentence_correction.10 | `Found: 9/9` | `No results in Антоненко-Давидович for: "Виправ лише наявні помилки й подай речення правильне збережи"` | `Found 1 results for: "Виправ лише наявні помилки й подай речення правильне збережи"`; `antonenko-davydovych-yak-my-hovorymo_p144` |
| C1.sentence_correction.11 | `Found: 10/10` | `No results in Антоненко-Давидович for: "Правильно запиши речення залишивши його без змін якщо помилок немає"` | `Found 1 results for: "Правильно запиши речення залишивши його без змін якщо помилок немає"`; `antonenko-davydovych-yak-my-hovorymo_p117` |
| C1.sentence_correction.12 | `Found: 10/10` | `No results in Антоненко-Давидович for: "За потреби виправ помилки а правильне речення залиш без змін"` | `Found 1 results for: "За потреби виправ помилки а правильне речення залиш без змін"`; `antonenko-davydovych-yak-my-hovorymo_p100` |
| C2.agreed_form.01 | `Found: 6/6` | `No results in Антоненко-Давидович for: "Подай форму слова за граматичним позначенням"` | `Found 1 results for: "Подай форму слова за граматичним позначенням"`; `antonenko-davydovych-yak-my-hovorymo_p023` |
| C2.agreed_form.02 | `Found: 4/4` | `No results in Антоненко-Давидович for: "Запиши слово у формі"` | `Found 1 results for: "Запиши слово у формі"`; `antonenko-davydovych-yak-my-hovorymo_p070` |
| C2.agreed_form.03 | `Found: 3/3` | `No results in Антоненко-Давидович for: "Наведи форму слова"` | `Found 1 results for: "Наведи форму слова"`; `antonenko-davydovych-yak-my-hovorymo_p023` |
| C2.agreed_form.04 | `Found: 3/3` | `No results in Антоненко-Давидович for: "Утвори форму слова"` | `Found 1 results for: "Утвори форму слова"`; `antonenko-davydovych-yak-my-hovorymo_p023` |
| C2.agreed_form.05 | `Found: 3/3` | `No results in Антоненко-Давидович for: "Добери форму слова"` | `Found 1 results for: "Добери форму слова"`; `antonenko-davydovych-yak-my-hovorymo_p023` |
| C2.agreed_form.06 | `Found: 3/3` | `No results in Антоненко-Давидович for: "Вкажи форму слова"` | `Found 1 results for: "Вкажи форму слова"`; `antonenko-davydovych-yak-my-hovorymo_p023` |
| C2.agreed_form.07 | `Found: 4/4` | `No results in Антоненко-Давидович for: "Слово постав у форму"` | `Found 1 results for: "Слово постав у форму"`; `antonenko-davydovych-yak-my-hovorymo_p101` |
| C2.agreed_form.08 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Яка форма слова відповідає позначенню"` | `Found 1 results for: "Яка форма слова відповідає позначенню"`; `antonenko-davydovych-yak-my-hovorymo_p047` |
| C2.agreed_form.09 | `Found: 7/7` | `No results in Антоненко-Давидович for: "Назви форму слова з таким граматичним позначенням"` | `Found 1 results for: "Назви форму слова з таким граматичним позначенням"`; `antonenko-davydovych-yak-my-hovorymo_p031` |
| C2.agreed_form.10 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Відтвори форму слова за позначенням"` | `Found 1 results for: "Відтвори форму слова за позначенням"`; `antonenko-davydovych-yak-my-hovorymo_p023` |
| C2.agreed_form.11 | `Found: 4/4` | `No results in Антоненко-Давидович for: "Постав слово у форму"` | `Found 1 results for: "Постав слово у форму"`; `antonenko-davydovych-yak-my-hovorymo_p101` |
| C2.agreed_form.12 | `Found: 8/8` | `No results in Антоненко-Давидович for: "Граматичне позначення потрібної форми слова Подай цю форму"` | `Found 1 results for: "Граматичне позначення потрібної форми слова Подай цю форму"`; `antonenko-davydovych-yak-my-hovorymo_p067` |
| C3.synonyms.03 | `Found: 6/6` | `No results in Антоненко-Давидович for: "Наведи синоніми до слова у значенні"` | `Found 1 results for: "Наведи синоніми до слова у значенні"`; `antonenko-davydovych-yak-my-hovorymo_p158` |
| C3.synonyms.09 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Відтвори синоніми слова у значенні"` | `Found 1 results for: "Відтвори синоніми слова у значенні"`; `antonenko-davydovych-yak-my-hovorymo_p158` |
| C3.synonyms.10 | `Found: 6/6` | `No results in Антоненко-Давидович for: "Перелічи синоніми до слова у значенні"` | `Found 1 results for: "Перелічи синоніми до слова у значенні"`; `antonenko-davydovych-yak-my-hovorymo_p158` |
| C3.synonyms.11 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Значення слова Наведи його синоніми"` | `Found 1 results for: "Значення слова Наведи його синоніми"`; `antonenko-davydovych-yak-my-hovorymo_p039` |
| C3.synonyms.12 | `Found: 7/7` | `No results in Антоненко-Давидович for: "У значенні слово має синоніми Назви їх"` | `Found 1 results for: "У значенні слово має синоніми Назви їх"`; `antonenko-davydovych-yak-my-hovorymo_p030` |
| C3.antonyms.03 | `Found: 6/6` | `No results in Антоненко-Давидович for: "Наведи антоніми до слова у значенні"` | `Found 1 results for: "Наведи антоніми до слова у значенні"`; `antonenko-davydovych-yak-my-hovorymo_p119` |
| C3.antonyms.09 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Відтвори антоніми слова у значенні"` | `Found 1 results for: "Відтвори антоніми слова у значенні"`; `antonenko-davydovych-yak-my-hovorymo_p119` |
| C3.antonyms.10 | `Found: 6/6` | `No results in Антоненко-Давидович for: "Перелічи антоніми до слова у значенні"` | `Found 1 results for: "Перелічи антоніми до слова у значенні"`; `antonenko-davydovych-yak-my-hovorymo_p119` |
| C3.antonyms.11 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Значення слова Наведи його антоніми"` | `Found 1 results for: "Значення слова Наведи його антоніми"`; `antonenko-davydovych-yak-my-hovorymo_p033` |
| C3.antonyms.12 | `Found: 7/7` | `No results in Антоненко-Давидович for: "У значенні слово має антоніми Назви їх"` | `Found 1 results for: "У значенні слово має антоніми Назви їх"`; `antonenko-davydovych-yak-my-hovorymo_p032` |
| C4.idiom_definition.01 | `Found: 10/10` | `No results in Антоненко-Давидович for: "Подай словникове значення вислову і цитату з тієї самої статті"` | `Found 1 results for: "Подай словникове значення вислову і цитату з тієї самої статті"`; `antonenko-davydovych-yak-my-hovorymo_p068` |
| C4.idiom_definition.02 | `Found: 11/11` | `No results in Антоненко-Давидович for: "Запиши значення вислову за словником разом із цитатою з цієї статті"` | `Found 1 results for: "Запиши значення вислову за словником разом із цитатою з цієї статті"`; `antonenko-davydovych-yak-my-hovorymo_p141` |
| C4.idiom_definition.03 | `Found: 12/12` | `No results in Антоненко-Давидович for: "Наведи словникове тлумачення вислову та його ілюстрацію цитату з тієї самої статті"` | `Found 1 results for: "Наведи словникове тлумачення вислову та його ілюстрацію цитату з тієї самої статті"`; `antonenko-davydovych-yak-my-hovorymo_p134` |
| C4.idiom_definition.04 | `Found: 12/12` | `No results in Антоненко-Давидович for: "Вкажи значення вислову і відтвори цитату наведену в тій самій словниковій статті"` | `Found 1 results for: "Вкажи значення вислову і відтвори цитату наведену в тій самій словниковій статті"`; `antonenko-davydovych-yak-my-hovorymo_p068` |
| C4.idiom_definition.05 | `Found: 11/11` | `No results in Антоненко-Давидович for: "Відтвори словникове тлумачення вислову разом із цитатою з цієї ж статті"` | `Found 1 results for: "Відтвори словникове тлумачення вислову разом із цитатою з цієї ж статті"`; `antonenko-davydovych-yak-my-hovorymo_p141` |
| C4.idiom_definition.06 | `Found: 11/11` | `No results in Антоненко-Давидович for: "Вислів подай його словникове значення та цитату з тієї самої статті"` | `Found 1 results for: "Вислів подай його словникове значення та цитату з тієї самої статті"`; `antonenko-davydovych-yak-my-hovorymo_p137` |
| C4.idiom_definition.07 | `Found: 11/11` | `No results in Антоненко-Давидович for: "Яке значення вислову подає словник Наведи також цитату з цієї статті"` | `Found 1 results for: "Яке значення вислову подає словник Наведи також цитату з цієї статті"`; `antonenko-davydovych-yak-my-hovorymo_p050` |
| C4.idiom_definition.08 | `Found: 12/12` | `No results in Антоненко-Давидович for: "Як словник тлумачить вислів Подай тлумачення і цитату з тієї ж статті"` | `Found 1 results for: "Як словник тлумачить вислів Подай тлумачення і цитату з тієї ж статті"`; `antonenko-davydovych-yak-my-hovorymo_p050` |
| C4.idiom_definition.09 | `Found: 10/10` | `No results in Антоненко-Давидович for: "Процитуй тлумачення вислову та ілюстративну цитату з однієї словникової статті"` | `Found 1 results for: "Процитуй тлумачення вислову та ілюстративну цитату з однієї словникової статті"`; `antonenko-davydovych-yak-my-hovorymo_p134` |
| C4.idiom_definition.10 | `Found: 12/12` | `No results in Антоненко-Давидович for: "Значення вислову запиши за словником і додай цитату з цієї самої статті"` | `Found 1 results for: "Значення вислову запиши за словником і додай цитату з цієї самої статті"`; `antonenko-davydovych-yak-my-hovorymo_p121` |
| C4.idiom_definition.11 | `Found: 11/11` | `No results in Антоненко-Давидович for: "Словникове тлумачення вислову наведи разом із цитатою з тієї ж статті"` | `Found 1 results for: "Словникове тлумачення вислову наведи разом із цитатою з тієї ж статті"`; `antonenko-davydovych-yak-my-hovorymo_p141` |
| C4.idiom_definition.12 | `Found: 14/14` | `No results in Антоненко-Давидович for: "Додай до словникового значення вислову цитату з тієї самої статті й подай обидва тексти"` | `Found 1 results for: "Додай до словникового значення вислову цитату з тієї самої статті й подай обидва тексти"`; `antonenko-davydovych-yak-my-hovorymo_p167` |
| C5.printed_spelling_rule.01 | `Found: 9/9` | `No results in Антоненко-Давидович for: "Подай повний текст параграфа Правопису у якому наведено приклад"` | `Found 1 results for: "Подай повний текст параграфа Правопису у якому наведено приклад"`; `antonenko-davydovych-yak-my-hovorymo_p147` |
| C5.printed_spelling_rule.02 | `Found: 8/8` | `No results in Антоненко-Давидович for: "Наведи дослівно параграф Правопису що містить такий приклад"` | `Found 1 results for: "Наведи дослівно параграф Правопису що містить такий приклад"`; `antonenko-davydovych-yak-my-hovorymo_p007` |
| C5.printed_spelling_rule.03 | `Found: 8/8` | `No results in Антоненко-Давидович for: "Запиши весь параграф Правопису у якому подано приклад"` | `Found 1 results for: "Запиши весь параграф Правопису у якому подано приклад"`; `antonenko-davydovych-yak-my-hovorymo_p151` |
| C5.printed_spelling_rule.04 | `Found: 8/8` | `No results in Антоненко-Давидович for: "Вкажи повний текст параграфа Правопису з таким прикладом"` | `Found 1 results for: "Вкажи повний текст параграфа Правопису з таким прикладом"`; `antonenko-davydovych-yak-my-hovorymo_p149` |
| C5.printed_spelling_rule.05 | `Found: 7/7` | `No results in Антоненко-Давидович for: "Відтвори весь параграф Правопису де наведено приклад"` | `Found 1 results for: "Відтвори весь параграф Правопису де наведено приклад"`; `antonenko-davydovych-yak-my-hovorymo_p147` |
| C5.printed_spelling_rule.06 | `Found: 10/10` | `No results in Антоненко-Давидович for: "Приклад із Правопису наведено далі Подай повний текст його параграфа"` | `Found 1 results for: "Приклад із Правопису наведено далі Подай повний текст його параграфа"`; `antonenko-davydovych-yak-my-hovorymo_p147` |
| C5.printed_spelling_rule.07 | `Found: 10/10` | `No results in Антоненко-Давидович for: "Який параграф Правопису містить такий приклад Наведи весь його текст"` | `Found 1 results for: "Який параграф Правопису містить такий приклад Наведи весь його текст"`; `antonenko-davydovych-yak-my-hovorymo_p149` |
| C5.printed_spelling_rule.08 | `Found: 10/10` | `No results in Антоненко-Давидович for: "Правопис містить наведений далі приклад Запиши дослівно весь відповідний параграф"` | `Found 1 results for: "Правопис містить наведений далі приклад Запиши дослівно весь відповідний параграф"`; `antonenko-davydovych-yak-my-hovorymo_p007` |
| C5.printed_spelling_rule.09 | `Found: 8/8` | `No results in Антоненко-Давидович for: "Процитуй повністю параграф Правопису у якому є приклад"` | `Found 1 results for: "Процитуй повністю параграф Правопису у якому є приклад"`; `antonenko-davydovych-yak-my-hovorymo_p151` |
| C5.printed_spelling_rule.10 | `Found: 10/10` | `No results in Антоненко-Давидович for: "Текст параграфа Правопису відтвори повністю за наведеним у ньому прикладом"` | `Found 1 results for: "Текст параграфа Правопису відтвори повністю за наведеним у ньому прикладом"`; `antonenko-davydovych-yak-my-hovorymo_p149` |
| C5.printed_spelling_rule.11 | `Found: 8/8` | `No results in Антоненко-Давидович for: "Дослівно наведи весь параграф Правопису що містить приклад"` | `Found 1 results for: "Дослівно наведи весь параграф Правопису що містить приклад"`; `antonenko-davydovych-yak-my-hovorymo_p007` |
| C5.printed_spelling_rule.12 | `Found: 8/8` | `No results in Антоненко-Давидович for: "Повністю запиши параграф Правопису у якому надруковано приклад"` | `Found 1 results for: "Повністю запиши параграф Правопису у якому надруковано приклад"`; `antonenko-davydovych-yak-my-hovorymo_p022` |
| C6.calque_correction.01 | `Found: 4/4` | `No results in Антоненко-Давидович for: "Виправ кальку в реченні"` | `Found 1 results for: "Виправ кальку в реченні"`; `antonenko-davydovych-yak-my-hovorymo_p141` |
| C6.calque_correction.02 | `Found: 4/4` | `No results in Антоненко-Давидович for: "Подай речення без кальки"` | `Found 1 results for: "Подай речення без кальки"`; `antonenko-davydovych-yak-my-hovorymo_p011` |
| C6.calque_correction.03 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Запиши наведене речення без кальки"` | `Found 1 results for: "Запиши наведене речення без кальки"`; `antonenko-davydovych-yak-my-hovorymo_p124` |
| C6.calque_correction.04 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Усунь кальку в наведеному реченні"` | `Found 1 results for: "Усунь кальку в наведеному реченні"`; `antonenko-davydovych-yak-my-hovorymo_p167` |
| C6.calque_correction.05 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Заміни калькований вислів у реченні"` | `Found 1 results for: "Заміни калькований вислів у реченні"`; `antonenko-davydovych-yak-my-hovorymo_p163` |
| C6.calque_correction.06 | `Found: 6/6` | `No results in Антоненко-Давидович for: "Наведи виправлений варіант речення з калькою"` | `Found 1 results for: "Наведи виправлений варіант речення з калькою"`; `antonenko-davydovych-yak-my-hovorymo_p112` |
| C6.calque_correction.07 | `Found: 4/4` | `No results in Антоненко-Давидович for: "Речення запиши без кальки"` | `Found 1 results for: "Речення запиши без кальки"`; `antonenko-davydovych-yak-my-hovorymo_p120` |
| C6.calque_correction.08 | `Found: 9/9` | `No results in Антоненко-Давидович for: "Як записати це речення без кальки Подай виправлений варіант"` | `Found 1 results for: "Як записати це речення без кальки Подай виправлений варіант"`; `antonenko-davydovych-yak-my-hovorymo_p152` |
| C6.calque_correction.09 | `Found: 4/4` | `No results in Антоненко-Давидович for: "Відредагуй речення усунувши кальку"` | `Found 1 results for: "Відредагуй речення усунувши кальку"`; `antonenko-davydovych-yak-my-hovorymo_p141` |
| C6.calque_correction.10 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Позбудься кальки й запиши речення"` | `Found 1 results for: "Позбудься кальки й запиши речення"`; `antonenko-davydovych-yak-my-hovorymo_p144` |
| C6.calque_correction.11 | `Found: 6/6` | `No results in Антоненко-Давидович for: "Правильно запиши речення замінивши калькований вислів"` | `Found 1 results for: "Правильно запиши речення замінивши калькований вислів"`; `antonenko-davydovych-yak-my-hovorymo_p117` |
| C6.calque_correction.12 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Без кальки подай наведене речення"` | `Found 1 results for: "Без кальки подай наведене речення"`; `antonenko-davydovych-yak-my-hovorymo_p124` |
| C6.book_calque_replacement.01 | `Found: 6/6` | `No results in Антоненко-Давидович for: "Подай заміну вислову яку пропонує автор"` | `Found 1 results for: "Подай заміну вислову яку пропонує автор"`; `antonenko-davydovych-yak-my-hovorymo_p121` |
| C6.book_calque_replacement.02 | `Found: 4/4` | `No results in Антоненко-Давидович for: "Наведи авторову заміну вислову"` | `Found 1 results for: "Наведи авторову заміну вислову"`; `antonenko-davydovych-yak-my-hovorymo_p121` |
| C6.book_calque_replacement.03 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Запиши заміну вислову за автором"` | `Found 1 results for: "Запиши заміну вислову за автором"`; `antonenko-davydovych-yak-my-hovorymo_p121` |
| C6.book_calque_replacement.04 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Вкажи заміну вислову наведену автором"` | `Found 1 results for: "Вкажи заміну вислову наведену автором"`; `antonenko-davydovych-yak-my-hovorymo_p068` |
| C6.book_calque_replacement.05 | `Found: 6/6` | `No results in Антоненко-Давидович for: "Відтвори заміну вислову яку подає автор"` | `Found 1 results for: "Відтвори заміну вислову яку подає автор"`; `antonenko-davydovych-yak-my-hovorymo_p121` |
| C6.book_calque_replacement.06 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Вислів яку заміну пропонує автор"` | `Found 1 results for: "Вислів яку заміну пропонує автор"`; `antonenko-davydovych-yak-my-hovorymo_p125` |
| C6.book_calque_replacement.07 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Яку заміну вислову подає автор"` | `Found 1 results for: "Яку заміну вислову подає автор"`; `antonenko-davydovych-yak-my-hovorymo_p121` |
| C6.book_calque_replacement.08 | `Found: 5/5` | `No results in Антоненко-Давидович for: "Як автор пропонує замінити вислів"` | `Found 1 results for: "Як автор пропонує замінити вислів"`; `antonenko-davydovych-yak-my-hovorymo_p125` |
| C6.book_calque_replacement.09 | `Found: 4/4` | `No results in Антоненко-Давидович for: "Процитуй авторову заміну вислову"` | `Found 1 results for: "Процитуй авторову заміну вислову"`; `antonenko-davydovych-yak-my-hovorymo_p121` |
| C6.book_calque_replacement.10 | `Found: 6/6` | `No results in Антоненко-Давидович for: "Заміни вислів так як пропонує автор"` | `Found 1 results for: "Заміни вислів так як пропонує автор"`; `antonenko-davydovych-yak-my-hovorymo_p163` |
| C6.book_calque_replacement.11 | `Found: 8/8` | `No results in Антоненко-Давидович for: "Заміна вислову є в автора Наведи її дослівно"` | `Found 1 results for: "Заміна вислову є в автора Наведи її дослівно"`; `antonenko-davydovych-yak-my-hovorymo_p121` |
| C6.book_calque_replacement.12 | `Found: 6/6` | `No results in Антоненко-Давидович for: "Автор подає заміну вислову Відтвори її"` | `Found 1 results for: "Автор подає заміну вислову Відтвори її"`; `antonenko-davydovych-yak-my-hovorymo_p121` |
| C7.modern_norm_selection.09 | `Found: 7/7` | `No results in Антоненко-Давидович for: "Випиши сучасну нормативну форму з поданої пари"` | `Found 1 results for: "Випиши сучасну нормативну форму з поданої пари"`; `antonenko-davydovych-yak-my-hovorymo_p066` |
| C7.modern_norm_selection.10 | `Found: 9/9` | `No results in Антоненко-Давидович for: "Форму що відповідає сучасній нормі обери з наведеної пари"` | `Found 1 results for: "Форму що відповідає сучасній нормі обери з наведеної пари"`; `antonenko-davydovych-yak-my-hovorymo_p120` |
| C7.modern_norm_selection.11 | `Found: 7/7` | `No results in Антоненко-Давидович for: "Сучасну нормативну форму запиши з наведеної пари"` | `Found 1 results for: "Сучасну нормативну форму запиши з наведеної пари"`; `antonenko-davydovych-yak-my-hovorymo_p042` |
| C7.modern_norm_selection.12 | `Found: 9/9` | `No results in Антоненко-Давидович for: "Із поданих форм назви ту що відповідає сучасній нормі"` | `Found 1 results for: "Із поданих форм назви ту що відповідає сучасній нормі"`; `antonenko-davydovych-yak-my-hovorymo_p168` |
| C8.supported_pronunciation.01 | `Found: 13/13` | `No results in Антоненко-Давидович for: "Подай нормативну або допустиму вимову слова та оцінку яку дає автор Фонетичний контекст"` | `Found 1 results for: "Подай нормативну або допустиму вимову слова та оцінку яку дає автор Фонетичний контекст"`; `antonenko-davydovych-yak-my-hovorymo_p131` |
| C8.supported_pronunciation.02 | `Found: 12/12` | `No results in Антоненко-Давидович for: "Запиши нормативну або допустиму вимову слова разом з авторовою оцінкою Контекст вимови"` | `Found 1 results for: "Запиши нормативну або допустиму вимову слова разом з авторовою оцінкою Контекст вимови"`; `antonenko-davydovych-yak-my-hovorymo_p125` |
| C8.supported_pronunciation.03 | `Found: 12/12` | `No results in Антоненко-Давидович for: "Наведи авторову оцінку й нормативну або допустиму вимову слова в такому контексті"` | `Found 1 results for: "Наведи авторову оцінку й нормативну або допустиму вимову слова в такому контексті"`; `antonenko-davydovych-yak-my-hovorymo_p138` |
| C8.supported_pronunciation.04 | `Found: 11/11` | `No results in Антоненко-Давидович for: "Вкажи нормативну або допустиму вимову слова і процитуй оцінку автора Контекст"` | `Found 1 results for: "Вкажи нормативну або допустиму вимову слова і процитуй оцінку автора Контекст"`; `antonenko-davydovych-yak-my-hovorymo_p129` |
| C8.supported_pronunciation.05 | `Found: 13/13` | `No results in Антоненко-Давидович for: "Відтвори нормативну або допустиму вимову слова та її оцінку автором у наведеному контексті"` | `Found 1 results for: "Відтвори нормативну або допустиму вимову слова та її оцінку автором у наведеному контексті"`; `antonenko-davydovych-yak-my-hovorymo_p050` |
| C8.supported_pronunciation.06 | `Found: 13/13` | `No results in Антоненко-Давидович for: "Слово має нормативну або допустиму вимову Подай її та оцінку автора Фонетичний контекст"` | `Found 1 results for: "Слово має нормативну або допустиму вимову Подай її та оцінку автора Фонетичний контекст"`; `antonenko-davydovych-yak-my-hovorymo_p129` |
| C8.supported_pronunciation.07 | `Found: 14/14` | `No results in Антоненко-Давидович for: "Яку вимову слова автор визнає нормативною або допустимою Наведи її та авторову оцінку Контекст"` | `Found 1 results for: "Яку вимову слова автор визнає нормативною або допустимою Наведи її та авторову оцінку Контекст"`; `antonenko-davydovych-yak-my-hovorymo_p025` |
| C8.supported_pronunciation.08 | `Found: 15/15` | `No results in Антоненко-Давидович for: "Як нормативно або допустимо вимовляти слово Подай вимову й оцінку яку дає автор Контекст вимови"` | `Found 1 results for: "Як нормативно або допустимо вимовляти слово Подай вимову й оцінку яку дає автор Контекст вимови"`; `antonenko-davydovych-yak-my-hovorymo_p129` |
| C8.supported_pronunciation.09 | `Found: 12/12` | `No results in Антоненко-Давидович for: "Процитуй оцінку автора й запиши нормативну або допустиму вимову слова Фонетичний контекст"` | `Found 1 results for: "Процитуй оцінку автора й запиши нормативну або допустиму вимову слова Фонетичний контекст"`; `antonenko-davydovych-yak-my-hovorymo_p129` |
| C8.supported_pronunciation.10 | `Found: 12/12` | `No results in Антоненко-Давидович for: "Дослівно відтвори нормативну або допустиму вимову слова разом з оцінкою автора Контекст"` | `Found 1 results for: "Дослівно відтвори нормативну або допустиму вимову слова разом з оцінкою автора Контекст"`; `antonenko-davydovych-yak-my-hovorymo_p007` |
| C8.supported_pronunciation.11 | `Found: 13/13` | `No results in Антоненко-Давидович for: "Нормативну або допустиму вимову слова наведи з авторовою оцінкою в такому фонетичному контексті"` | `Found 1 results for: "Нормативну або допустиму вимову слова наведи з авторовою оцінкою в такому фонетичному контексті"`; `antonenko-davydovych-yak-my-hovorymo_p138` |
| C8.supported_pronunciation.12 | `Found: 12/12` | `No results in Антоненко-Давидович for: "Оцінку автора подай разом із нормативною або допустимою вимовою слова Контекст вимови"` | `Found 1 results for: "Оцінку автора подай разом із нормативною або допустимою вимовою слова Контекст вимови"`; `antonenko-davydovych-yak-my-hovorymo_p129` |
| C9.verbatim_section.01 | `Found: 11/11` | `No results in Антоненко-Давидович for: "Подай дослівно текст під таким заголовком Підручник клас або рівень заголовок"` | `Found 1 results for: "Подай дослівно текст під таким заголовком Підручник клас або рівень заголовок"`; `antonenko-davydovych-yak-my-hovorymo_p007` |
| C9.verbatim_section.02 | `Found: 13/13` | `No results in Антоненко-Давидович for: "Наведи текст під надрукованим заголовком без змін Назва підручника клас або рівень заголовок"` | `Found 1 results for: "Наведи текст під надрукованим заголовком без змін Назва підручника клас або рівень заголовок"`; `antonenko-davydovych-yak-my-hovorymo_p164` |
| C9.verbatim_section.03 | `Found: 12/12` | `No results in Антоненко-Давидович for: "Відтвори повністю текст під заголовком із підручника Назва заголовок клас або рівень"` | `Found 1 results for: "Відтвори повністю текст під заголовком із підручника Назва заголовок клас або рівень"`; `antonenko-davydovych-yak-my-hovorymo_p164` |
| C9.verbatim_section.04 | `Found: 13/13` | `No results in Антоненко-Давидович for: "Запиши дослівно текст під заголовком у зазначеному підручнику Клас або рівень підручник заголовок"` | `Found 1 results for: "Запиши дослівно текст під заголовком у зазначеному підручнику Клас або рівень підручник заголовок"`; `antonenko-davydovych-yak-my-hovorymo_p007` |
| C9.verbatim_section.05 | `Found: 11/11` | `No results in Антоненко-Давидович for: "Процитуй увесь текст під таким заголовком Заголовок підручник клас або рівень"` | `Found 1 results for: "Процитуй увесь текст під таким заголовком Заголовок підручник клас або рівень"`; `antonenko-davydovych-yak-my-hovorymo_p164` |
| C9.verbatim_section.06 | `Found: 14/14` | `No results in Антоненко-Давидович for: "Заголовок надруковано в підручнику Подай весь текст під ним Заголовок клас або рівень назва підручника"` | `Found 1 results for: "Заголовок надруковано в підручнику Подай весь текст під ним Заголовок клас або рівень назва підручника"`; `antonenko-davydovych-yak-my-hovorymo_p164` |
| C9.verbatim_section.07 | `Found: 14/14` | `No results in Антоненко-Давидович for: "Який текст надруковано під цим заголовком Відтвори його повністю Підручник клас або рівень заголовок"` | `Found 1 results for: "Який текст надруковано під цим заголовком Відтвори його повністю Підручник клас або рівень заголовок"`; `antonenko-davydovych-yak-my-hovorymo_p022` |
| C9.verbatim_section.08 | `Found: 13/13` | `No results in Антоненко-Давидович for: "Що написано під наведеним заголовком Процитуй увесь текст Клас або рівень заголовок підручник"` | `Found 1 results for: "Що написано під наведеним заголовком Процитуй увесь текст Клас або рівень заголовок підручник"`; `antonenko-davydovych-yak-my-hovorymo_p144` |
| C9.verbatim_section.09 | `Found: 11/11` | `No results in Антоненко-Давидович for: "Дослівно наведи текст під заголовком Назва підручника заголовок клас або рівень"` | `Found 1 results for: "Дослівно наведи текст під заголовком Назва підручника заголовок клас або рівень"`; `antonenko-davydovych-yak-my-hovorymo_p164` |
| C9.verbatim_section.10 | `Found: 11/11` | `No results in Антоненко-Давидович for: "Текст під заголовком відтвори без скорочень Клас або рівень підручник заголовок"` | `Found 1 results for: "Текст під заголовком відтвори без скорочень Клас або рівень підручник заголовок"`; `antonenko-davydovych-yak-my-hovorymo_p164` |
| C9.verbatim_section.11 | `Found: 11/11` | `No results in Антоненко-Давидович for: "Повністю запиши текст під таким заголовком Заголовок підручник клас або рівень"` | `Found 1 results for: "Повністю запиши текст під таким заголовком Заголовок підручник клас або рівень"`; `antonenko-davydovych-yak-my-hovorymo_p164` |
| C9.verbatim_section.12 | `Found: 14/14` | `No results in Антоненко-Давидович for: "Без змін подай увесь текст під надрукованим заголовком Клас або рівень заголовок назва підручника"` | `Found 1 results for: "Без змін подай увесь текст під надрукованим заголовком Клас або рівень заголовок назва підручника"`; `antonenko-davydovych-yak-my-hovorymo_p164` |

The four `для` fixes follow both the structured article and the full-book
surface, not only Russian-shadow morphology. Supplemental calls:

`search_style_guide(query="Для, задля, на, про, під, до")`:

```text
Found 1 results in **Антоненко-Давидович** for: "Для, задля, на, про, під, до"
```

`search_text(query="Для, задля, на, про, під, до", source_file="antonenko-davydovych-yak-my-hovorymo")`:

```text
Found 1 results for: "Для, задля, на, про, під, до"
```

### Reproduction

From the assigned worktree, use the task-prescribed shared interpreter as
`LU_PROJECT_PYTHON`; never create a worktree virtualenv. For source calls, start
`.mcp/servers/sources/server.py` with that interpreter through the MCP stdio
client; use the task's canonical database and scratch logging overrides.
Authenticate with `mcp_server_identity`, then call `query_pravopys` (§§23, 155,
160, 164), `verify_words` and both per-line searches as specified above.
The Sources MCP transport and canonical database, not the connected stale
instance, determine these responses.

```bash
"$LU_PROJECT_PYTHON" -m pytest tests/projects/open_model_data/test_instruction_catalog.py -q
"$LU_PROJECT_PYTHON" -m ruff check tests/projects/open_model_data/test_instruction_catalog.py
"$LU_PROJECT_PYTHON" -m yamllint registry/projects/open_model_data/instruction_catalog.yaml
git diff --check
```

Executed in the assigned dispatch worktree with the task-prescribed shared
interpreter. Final scoped pytest output:

```text
337 passed in 10.03s
```

The first run in the owned test directory was skipped by the repository's
`data/projects` sparse-tree guard. After `git sparse-checkout add data/projects`,
all 337 cases ran and passed; no skip rule or test expectation was changed.
Ruff check returned `All checks passed!`; Ruff format check returned
`1 file already formatted`. YAML lint and `git diff --check` exited 0 without
output. No other importing consumer was found by the scoped Python-source
search for `instruction_catalog`; no full test suite was collected.

## Round 3 finding disposition and source evidence

| Finding | Resolution and line IDs |
| --- | --- |
| B1 | C2.agreed_form.01–12: fixed `c2-header-cells.v1`; explicit source fields/locators; visible `{sense}`; conflicting or missing sense withheld; all variants in one target. Conservative ULIF field census above. |
| S1 / Flash FIX | C2.agreed_form.08: `?` follows `{slot}` before the final sense block. |
| S2 | C2 .01–12 and both C3 operations .01–12: final unquoted `Значення: {sense}`; six punctuation/parenthesis fixtures and quotation mutations. |
| S3 | C6.book_calque_replacement.01–12: one/multiple replacements or neutral `замінити`; .08/.10 already neutral. |
| N1 | C8.supported_pronunciation.05: `та авторову оцінку`. |
| N2 | Per-operation 4-/5-/6-gram prevalence above, diagnostic only; stricter 0.15/0.60 retained. |
| N3 | C1.sentence_correction.10/.12: final conditional `якщо воно правильне`. |

Sources MCP calls in this round (source roles differ):

- `verify_words` on the 81 distinct authored words from the 49 changed lines:
  **`Found: 81/81`**. Follow-up for `врахуй`, `і`: **`Found: 2/2`**.
  These attest morphology, not whole-sentence naturalness.
- `query_pravopys(topic="156")`, official authorized edition, §156 pp.199–201:
  **`1. У кінці питального речення`**. This is punctuation authority for S1.
- `query_pravopys(topic="164")`, §164 pp.246–248, Примітка 1:
  **`двокрапка й тире, ніколи не ставимо перед закритими лапками`**.
  S2 avoids wrapping source glosses instead of rewriting their punctuation.
- `search_style_guide(query="вірний", limit=1)`:
  **`Found 1 results in **Антоненко-Давидович** for: "вірний"`**.
  Structured source hit explicitly lists several context-bound replacements;
  full hit includes `на певну загибель`, `правдивий шлях` and
  `слушно робить син`. It supports replacement multiplicity, not every
  authored instruction's naturalness.
- `search_text(query="вірний", source_file="antonenko-davydovych-yak-my-hovorymo", limit=1)`:
  **`Found 1 results for: "вірний"`**, chunk
  `antonenko-davydovych-yak-my-hovorymo_p051`, independently supplies the
  book passage with those replacements.
- `search_style_guide(query="орудний", limit=1)`:
  **`Found 1 results in **Антоненко-Давидович** for: "орудний"`**,
  headword `Орудний відмінок дійової особи й знаряддя`.
  `search_text(query="орудний", source_file="antonenko-davydovych-yak-my-hovorymo", limit=1)`:
  **`Found 1 results for: "орудний"`**, chunk `_p014` (time, not agent usage).
  A narrower full-book query, `search_text(query="Енеєм",
  source_file="antonenko-davydovych-yak-my-hovorymo", limit=1)`, returned
  **`Found 1 results for: "Енеєм"`**, chunk `_p013`: the relevant agent-case
  paragraph says **`але не треба й надуживати ним`**. This supports N1's
  stylistic simplification; VESUM attests `авторову`.
  `search_style_guide(query="авторову", limit=1)` returned
  **`No results in Антоненко-Давидович for: "авторову"`**; absence is not approval.
- `check_russian_shadow(word="авторову")` and `check_russian_shadow(word="заміни")`:
  **`"matches_russian": false`**, **`"confidence": 0.0`** each.
  These are suspicion checks, not calque verdicts. No Russianism judgment is
  inferred from them.

Earlier evidence above is historical round-2 evidence for the previous
catalog revision; it does not approve the round-3 head. No independent
held-out or fresh exact-head reviewer proof is claimed by these author checks.

## Round 3 scoped validation

Executed from the assigned dispatch worktree with the shared project
interpreter. Only the owned test file imports this catalog, per
`rg -n 'instruction_catalog' tests -g '*.py'`; no full suite was collected.

```bash
"$LU_PROJECT_PYTHON" -m pytest tests/projects/open_model_data/test_instruction_catalog.py -q
# 367 passed in 13.97s
"$LU_PROJECT_RUFF" check tests/projects/open_model_data/test_instruction_catalog.py
# All checks passed!
"$LU_PROJECT_PYTHON" -m yamllint registry/projects/open_model_data/instruction_catalog.yaml
# exit 0, no output
git diff --check
# exit 0, no output
```

New cases retain all prior slot mutations and add missing serializer/sense,
metadata-only sense, free-form joins, first-variant targets, ambiguous empty
senses, empty/code-only headers, noun/verb header shapes and complete-variant
JSON round trips. For each of six punctuation/parenthesis values, every sense
line is rendered and its quoted-slot mutation rejected. These are local
schema/interpolation/arithmetic fixtures, **not** independent held-out proof.
The production relationship checker remains E5's deliverable.

## Driver handback and stopping rule

The worker milestone is a pushed review-fix branch with clean status, not issue
closure. The catalog denominator remains C1–C9 (9 components, 132 lines).
The accountable `claude-open-model-data` driver owns:

1. Fresh exact-head non-author language/semantic reviews and code CF where
   applicable. Prior reviews of e3eed1e5 do not approve this revision.
2. Freeze catalog bytes/hash and the metric protocol before E12 after those
   reviews; retain the adopted 0.15/0.60 bounds and verify scheduling feasibility
   in each source eligibility stratum.
3. E4 source-field authentication: C2 header-cell locators/visible senses and
   complete variant agreement, C3 sense labels, C8
   context/author identity and C9 printed headings/position from #8341.
   Sparse label availability means withholding, never inferred labels.
4. E5-backed production checker with independently executed negative fixtures;
   the local arithmetic test cannot satisfy that production gate or D4.
5. PR, CI, merge, issue closeout and cleanup via the existing driver flow.

This is the last authoring round before the PR. B1/S1/S2/S3 have concrete
resolutions above; missing exact-head review remains the driver's gate.
Unresolved source/meaning/grammar findings block acceptance. If reviewers still disagree after tool-backed resolution, drop the
line per the issue policy; recheck 10–12 lines/operation, source eligibility and
metric feasibility. A missing required component, infeasible bucket or missing
source field is withheld and stays open with the driver as owner. New finding
classes require a changed approach, never a lowered bar. No two-seat approval,
final catalog/protocol freeze, production checker or independent held-out proof is claimed. The driver owns these residual gates;
this worker stops at the pushed clean branch, without opening a PR.
