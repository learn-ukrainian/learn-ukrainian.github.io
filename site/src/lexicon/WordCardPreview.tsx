import type { ReactNode } from 'react';
import { compareCurrent, type PreviewCard } from '../lib/lexicon/word-card-preview';
import type { EntryRecord } from '../lib/lexicon/atlas-data-source';
import { attributionGap, attributionLinks, releaseAccounting, releaseReportUrl, type LoadedRelease, type ReleaseCard, type ReleaseIndex, type ReleaseRow } from '../lib/lexicon/word-card-release';
import { groupReleasePages, pagePath, readableEntry, sourceCredits, type Credit, type FactGroup, type ParadigmCell, type ParadigmTable, type ReadableEntry, type ReleasePage, type SlotLabel } from '../lib/lexicon/word-card-readable';

function Accounting({ rows, scope, learner = false }: Pick<LoadedRelease, 'rows'> & { scope: string; learner?: boolean }) {
  const { attributionGaps, ...coverage } = releaseAccounting(rows);
  return <section aria-label={`Measured coverage of ${scope}`}><h3>Measured coverage of {scope}</h3>
    <pre data-release-accounting>{JSON.stringify(learner ? coverage : { ...coverage, attributionGaps }, null, 2)}</pre>
    <p>Absent field classes are measured separately from producer-declared gaps. No declared gaps does not establish completeness.</p>
    {!learner && <p>Attribution gaps remain owned by Data. Source strings are preserved, including placeholders.</p>}
  </section>;
}

function WithdrawalBanner({ notice }: { notice: LoadedRelease['withdrawalNotice'] }) {
  if (notice === undefined) return null;
  const removed = typeof notice === 'object' && notice !== null && !Array.isArray(notice) && typeof notice.removed_field_citations === 'number'
    ? notice.removed_field_citations : null;
  return <aside role="note" className="wc-withdrawal-banner" data-withdrawal-warning>
    Withdrawal notice active{removed !== null ? ` (${removed} field citations removed)` : ''}. Full notice is in Sources and audit.
  </aside>;
}

function WithdrawalNotice({ notice }: { notice: LoadedRelease['withdrawalNotice'] }) {
  return notice === undefined ? null : <section aria-label="Withdrawal notice"><h3>Withdrawal notice</h3>
    <pre>{JSON.stringify(notice, null, 2)}</pre>
  </section>;
}

const assertionTarget = (assertionId: string) => `assertion-${encodeURIComponent(assertionId)}`;
const sourceTarget = (sourceId: string) => `source-${encodeURIComponent(sourceId)}`;

function AssertionRecord({ card, field, learner = false }: { card: ReleaseCard; field: ReleaseRow['fields'][number]; learner?: boolean }) {
  return <article id={learner ? undefined : assertionTarget(field.assertion_id)} data-release-assertion={field.assertion_id}>
    <h4>{field.field}</h4><p>{field.subject.kind}: {field.subject.id}</p>
    <pre data-raw-value>{typeof field.value === 'string' ? field.value : JSON.stringify(field.value, null, 2)}</pre>
    {learner ? <>
      <dl className="wc-binding"><dt>Assertion</dt><dd>{field.assertion_id}</dd>
        <dt>Source</dt><dd data-assertion-source>{field.citation.source_id}</dd>
        <dt>Snapshot</dt><dd data-assertion-snapshot>{field.citation.snapshot_id}</dd>
        <dt>Locator</dt><dd data-assertion-locator>{field.citation.locator}</dd></dl>
      <a data-raw-diagnostic href={`/lexicon-v2/release/${encodeURIComponent(card.row.card_id)}/#${assertionTarget(field.assertion_id)}`}>Inspect original citation</a>
    </> : <><pre data-release-citation>{JSON.stringify(field.citation, null, 2)}</pre>
    <p data-source-attribution>{field.citation.attribution}</p>
    {attributionLinks(field.citation.attribution).map(url => <a data-source-link key={url} href={url}>{url}</a>)}
    {attributionGap(field.citation) && <p data-attribution-gap={attributionGap(field.citation)}>Attribution gap: {attributionGap(field.citation)}. Owner Data. Placeholder retained verbatim.</p>}
    </>}
    <a data-report-action href={releaseReportUrl(card, field)}>Report / improve this assertion</a>
  </article>;
}

const FIELD_LABELS: Record<string, string> = { spelling: 'Spelling', mwe_form: 'Expression', stress: 'Stress', pos: 'Part of speech',
  gender: 'Gender', aspect: 'Aspect', grammatical_label: 'Grammar', cefr: 'CEFR level', sense_label: 'Sense',
  definition_uk: 'Meaning', synonyms: 'Synonyms', antonyms: 'Antonyms' };
const UKRAINIAN_FIELDS = new Set(['spelling', 'mwe_form', 'stress', 'grammatical_label', 'sense_label', 'definition_uk', 'synonyms', 'antonyms']);
const CORE_FACT_ORDER = ['spelling', 'mwe_form', 'stress', 'pos', 'gender', 'aspect', 'grammatical_label', 'cefr'] as const;
const SENSE_FIELD_ORDER = ['sense_label', 'definition_uk', 'synonyms', 'antonyms'];
const KIND_LABELS: Record<string, string> = { lexeme: 'Word', mwe: 'Multi-word expression', proper_name: 'Proper name' };
const capital = (text: string) => text.charAt(0).toUpperCase() + text.slice(1);

const isNonEmptyString = (value: unknown): value is string => typeof value === 'string' && value.trim().length > 0;
const isNonEmptyStringArray = (value: unknown): value is string[] => Array.isArray(value) && value.length > 0 && value.every(isNonEmptyString);

export function isUsableFieldValue(field: string, value: ReleaseRow['fields'][number]['value']): boolean {
  switch (field) {
    case 'spelling':
    case 'mwe_form':
    case 'pos':
    case 'aspect':
    case 'grammatical_label':
    case 'cefr':
    case 'sense_label':
    case 'definition_uk':
      return isNonEmptyString(value);
    case 'stress':
    case 'gender':
      return isNonEmptyString(value) || isNonEmptyStringArray(value);
    case 'synonyms':
    case 'antonyms':
      return isNonEmptyString(value)
        || isNonEmptyStringArray(value)
        || (value !== null && typeof value === 'object' && !Array.isArray(value) && isNonEmptyString(value.members));
    case 'paradigm':
      return value !== null && typeof value === 'object' && !Array.isArray(value)
        && isNonEmptyString(value.slot)
        && Array.isArray(value.forms)
        && value.forms.some(isNonEmptyString);
    default:
      return isNonEmptyString(value) || isNonEmptyStringArray(value);
  }
}

export function cardHeading(entry: ReadableEntry): { title: string; heading: string; hasText: boolean } {
  const { row } = entry;
  const nameField = row.card_kind === 'mwe' ? 'mwe_form' : 'spelling';
  const onCard = (field: ReleaseRow['fields'][number]) => field.subject.kind === 'card' && field.subject.id === row.card_id;
  const usableStrings = (fieldName: string) => [...new Set(
    row.fields
      .filter(field => onCard(field) && field.field === fieldName && isUsableFieldValue(fieldName, field.value))
      .map(field => Array.isArray(field.value) ? (field.value as string[]).join(', ') : (field.value as string)),
  )];
  const names = usableStrings(nameField);
  const stresses = usableStrings('stress');
  if (names.length > 1) {
    const joined = names.join(' / ');
    return { title: joined, heading: joined, hasText: true };
  }
  if (stresses.length === 1) {
    return { title: names[0] ?? stresses[0]!, heading: stresses[0]!, hasText: true };
  }
  if (names.length === 1) {
    return { title: names[0]!, heading: names[0]!, hasText: true };
  }
  if (stresses.length > 1) {
    const joined = stresses.join(' / ');
    return { title: joined, heading: joined, hasText: true };
  }
  return { title: 'Headword missing', heading: 'Headword missing', hasText: false };
}

function usableAssertionIds(row: ReleaseRow): Set<string> {
  return new Set(row.fields.filter(field => isUsableFieldValue(field.field, field.value)).map(field => field.assertion_id));
}

function hasUsableFact(group: FactGroup, usableIds: Set<string>): boolean {
  return group.facts.some(fact => fact.assertionIds.some(id => usableIds.has(id)));
}

function missingCoreFields(entry: ReadableEntry, usableIds: Set<string>): string[] {
  const usableFields = new Set(entry.facts.filter(group => hasUsableFact(group, usableIds)).map(group => group.field));
  const posTokens = new Set(
    (entry.facts.find(group => group.field === 'pos')?.facts ?? [])
      .filter(fact => fact.assertionIds.some(id => usableIds.has(id)))
      .flatMap(fact => fact.value.toLowerCase().split(',').map(token => token.trim()))
      .filter(Boolean),
  );
  const expected = [
    entry.row.card_kind === 'mwe' ? 'mwe_form' : 'spelling',
    'stress',
    'pos',
    ...(posTokens.has('noun') ? ['gender'] : []),
    ...(posTokens.has('verb') ? ['aspect'] : []),
    'cefr',
  ];
  return expected.filter(field => !usableFields.has(field));
}

function Credits({ credits }: { credits: Credit[] }) {
  return <span className="wc-credits" data-credits>Source: {[...new Set(credits.map(c => c.sourceId))].map((sourceId, i) =>
    <span key={sourceId}>{i > 0 && ', '}<a data-credit-ref href={`#${sourceTarget(sourceId)}`}>{sourceId}</a></span>)}</span>;
}

function PageCredits({ rows, pin }: Pick<LoadedRelease, 'rows' | 'pin'>) {
  return <section aria-label="Source credits"><h3>Source credits</h3>
    <ul className="wc-source-list">{sourceCredits(rows, pin).map(source => <li id={sourceTarget(source.sourceId)} key={source.sourceId} data-source-credit={source.sourceId}>
      <h4>{source.sourceId}</h4>
      {source.attributions.map(text => <p data-credit-attribution key={text}>{text}</p>)}
      {source.links.map(url => <p key={url}><a data-credit-link href={url}>{url}</a></p>)}
      {source.licences.map((licence, i) => <p data-credit-licence key={i}>Licence: {typeof licence === 'string' ? licence : JSON.stringify(licence)}</p>)}
    </li>)}</ul>
  </section>;
}

function Facts({ groups, missing = [], usableIds }: { groups: FactGroup[]; missing?: string[]; usableIds?: Set<string> }) {
  const byField = new Map(groups.map(group => [group.field, group]));
  const missingSet = new Set(missing);
  const core = new Set<string>(CORE_FACT_ORDER);
  const orderedFields = [
    ...CORE_FACT_ORDER.filter(field => byField.has(field) || missingSet.has(field)),
    ...groups.map(group => group.field).filter(field => !core.has(field)),
    ...missing.filter(field => !core.has(field) && !byField.has(field)),
  ];
  if (orderedFields.length === 0) return null;
  return <dl className="wc-facts">{orderedFields.flatMap(field => {
    const group = byField.get(field);
    if (!group) {
      return [<div key={`missing-${field}`} data-missing-field={field}>
        <dt>{FIELD_LABELS[field] ?? field}</dt>
        <dd className="wc-missing" data-missing-value>Missing — not supplied in this release</dd>
      </div>];
    }
    const items = [<div key={group.field} data-fact={group.field}>
      <dt>{FIELD_LABELS[group.field] ?? group.field}</dt>
      {group.facts.map((fact, i) => {
        const usable = !usableIds || fact.assertionIds.some(id => usableIds.has(id));
        return <dd key={i} data-assertions={fact.assertionIds.join(' ')}>
          <span data-fact-value className={group.field === 'cefr' && usable ? 'wc-cefr-badge' : undefined}
            lang={UKRAINIAN_FIELDS.has(group.field) && usable ? 'uk' : undefined}>{fact.value}</span> <Credits credits={fact.credits} />
        </dd>;
      })}
      {group.facts.length > 1 && <dd className="wc-note" data-sources-differ>Sources differ. Each value is shown with its own source; no value is chosen.</dd>}
    </div>];
    if (missingSet.has(group.field)) {
      items.push(<div key={`missing-${field}`} data-missing-field={field}>
        <dt>{FIELD_LABELS[field] ?? field} (status)</dt>
        <dd className="wc-missing" data-missing-value>Missing — no usable value supplied in this release</dd>
      </div>);
    }
    return items;
  })}</dl>;
}

function Label({ label }: { label: SlotLabel }) {
  return label.unknown ? <><code>{label.text}</code> (unrecognised slot code, shown literally)</> : <span lang="uk">{capital(label.text)}</span>;
}

function Cell({ cell }: { cell: ParadigmCell | null }) {
  if (!cell) return <td><span aria-hidden="true">—</span><span className="wc-sr-only">not supplied</span></td>;
  const forms = cell.forms.filter(isNonEmptyString);
  return forms.length > 0
    ? <td lang="uk" data-assertions={cell.assertionIds.join(' ')}>{forms.join(', ')}</td>
    : <td data-assertions={cell.assertionIds.join(' ')}><span aria-hidden="true">—</span><span className="wc-sr-only">no usable form supplied</span></td>;
}

/** Focusable labelled scroll region, so a wide table stays keyboard-reachable on narrow screens. */
function Scroll({ label, children }: { label: string; children: ReactNode }) {
  return <div className="wc-table" role="region" aria-label={label} tabIndex={0}>{children}</div>;
}

function Paradigm({ table }: { table: ParadigmTable }) {
  return <section className="wc-paradigm" data-paradigm-source={table.sourceId} aria-label={`Forms from ${table.sourceId}`}>
    <h4><Credits credits={table.credits} /></h4>
    {table.caseRows.length > 0 && <Scroll label={`Case forms from ${table.sourceId}`}><table>
      <thead><tr><th scope="col" lang="uk">Відмінок</th>{table.columns.map(c => <th scope="col" key={c.key}><Label label={c.label} /></th>)}</tr></thead>
      <tbody>{table.caseRows.map(row => <tr key={row.label}><th scope="row" lang="uk">{row.label}</th>
        {row.cells.map((cell, i) => <Cell key={i} cell={cell} />)}</tr>)}</tbody>
    </table></Scroll>}
    {table.formRows.length > 0 && <Scroll label={`Other forms from ${table.sourceId}`}><table>
      <thead><tr><th scope="col">Grammatical form</th><th scope="col">Supplied forms</th></tr></thead>
      <tbody>{table.formRows.map(row => <tr key={row.slot}><th scope="row"><Label label={row.label} /></th><Cell cell={row.cell} /></tr>)}</tbody>
    </table></Scroll>}
  </section>;
}

function EntryContent({ entry, labelSuffix }: { entry: ReadableEntry; labelSuffix?: string }) {
  const usableIds = usableAssertionIds(entry.row);
  const cardDefinitions = entry.other.filter(group => group.field === 'definition_uk');
  const otherFacts = entry.other.filter(group => group.field !== 'definition_uk');
  const senseLabelGroups = entry.senses.flatMap(sense => sense.groups.filter(group => group.field === 'sense_label'));
  const definitionGroups = [...cardDefinitions, ...entry.senses.flatMap(sense => sense.groups.filter(group => group.field === 'definition_uk'))];
  const hasSenseLabel = senseLabelGroups.some(group => hasUsableFact(group, usableIds));
  const hasDefinition = definitionGroups.some(group => hasUsableFact(group, usableIds));
  const missing = missingCoreFields(entry, usableIds);
  const orderedSenses = entry.senses.map(sense => ({
    ...sense,
    groups: [...sense.groups].sort((a, b) => {
      const ai = SENSE_FIELD_ORDER.indexOf(a.field);
      const bi = SENSE_FIELD_ORDER.indexOf(b.field);
      return (ai < 0 ? SENSE_FIELD_ORDER.length : ai) - (bi < 0 ? SENSE_FIELD_ORDER.length : bi);
    }),
  }));
  const hasUsableParadigm = entry.paradigms.some(table =>
    table.caseRows.some(row => row.cells.some(cell => cell !== null && cell.forms.some(isNonEmptyString)))
    || table.formRows.some(row => row.cell.forms.some(isNonEmptyString)),
  );
  return <>
    <Facts groups={entry.facts} missing={missing} usableIds={usableIds} />
    <section aria-label={labelSuffix ? `Senses of ${labelSuffix}` : 'Senses and meaning'}>
      <h3>Senses and meaning</h3>
      {orderedSenses.length > 0 && <ol className="wc-senses">
        {orderedSenses.map(sense => <li key={sense.id} data-sense={sense.id}><Facts groups={sense.groups} usableIds={usableIds} /></li>)}
      </ol>}
      {cardDefinitions.length > 0 && <Facts groups={cardDefinitions} usableIds={usableIds} />}
      {!hasSenseLabel && <p className="wc-missing" data-missing-field="sense_label">
        Sense labels: Missing — {senseLabelGroups.length > 0 ? 'no usable value supplied in this release.' : 'not supplied in this release.'}
      </p>}
      {!hasDefinition && <p className="wc-missing" data-missing-field="definition_uk">
        Meaning: Missing — {definitionGroups.length > 0 ? 'no usable value supplied in this release.' : 'not supplied in this release.'}
      </p>}
    </section>
    <section aria-label={labelSuffix ? `Forms of ${labelSuffix}` : 'Forms'}>
      <h3>Forms</h3>
      {entry.paradigms.map(t => <Paradigm key={t.sourceId} table={t} />)}
      {!hasUsableParadigm && <p className="wc-missing" data-missing-paradigm>
        {entry.paradigms.length > 0
          ? 'No usable paradigm forms are supplied for this entry in this release. Forms are not borrowed from other entries.'
          : 'No paradigm is supplied for this entry in this release. Forms are not borrowed from other entries.'}
      </p>}
    </section>
    {otherFacts.length > 0 && <section aria-label={labelSuffix ? `Other source facts of ${labelSuffix}` : 'Other source facts'}>
      <h3>Other source facts</h3>
      <p>Shown literally. This preview has no readable layout for these fields yet.</p><Facts groups={otherFacts} usableIds={usableIds} />
    </section>}
  </>;
}

function Entry({ entry, pin }: { entry: ReadableEntry; pin: ReleasePage['pin'] }) {
  const { row, ordinal } = entry;
  const head = cardHeading(entry);
  const usableIds = usableAssertionIds(row);
  const senseLabels = entry.senses.flatMap(s => s.groups.filter(g => g.field === 'sense_label')
    .flatMap(g => g.facts.filter(f => f.assertionIds.some(id => usableIds.has(id))).map(f => f.value)));
  return <article className="wc-entry" data-entry={row.card_id} data-entry-kind={row.card_kind} aria-labelledby={`entry-${row.card_id}`}>
    <h2 id={`entry-${row.card_id}`}><span className="wc-ordinal">{ordinal}.</span> <span lang={head.hasText ? 'uk' : undefined}>{head.heading}</span></h2>
    <p className="wc-kind" data-entry-label>{KIND_LABELS[row.card_kind] ?? row.card_kind}
      {entry.proper && <> — {senseLabels.length ? <span lang="uk">{senseLabels.join('; ')}</span> : 'no sense label supplied'}. Listed after common entries.</>}
      {' '}<span className="wc-status" data-entry-status>{row.status}</span></p>
    <EntryContent entry={entry} labelSuffix={`entry ${ordinal}`} />
    <details className="wc-audit" data-entry-audit={row.card_id}><summary>Sources and audit details for entry {ordinal}</summary>
      <p>Card <code>{row.card_id}</code>, card version <code data-card-version>{row.card_version}</code>, producer status {row.status}.</p>
      <section aria-label={`Known gaps of entry ${ordinal}`}><h3>Known gaps</h3><p>Declared metadata, not language facts.</p>
        {row.known_gaps.length ? row.known_gaps.map((gap, i) => <pre key={i}>{typeof gap === 'string' ? gap : JSON.stringify(gap, null, 2)}</pre>) : <p>No declared gaps</p>}
      </section>
      <Accounting rows={[row]} scope="this entry" learner />
      <h3>Cited assertions</h3><p>Assertions remain separate. No field resolution or semantic verdict is inferred.</p>
      {row.fields.map(field => <AssertionRecord key={field.assertion_id} card={{ kind: 'release-card', row, pin }} field={field} learner />)}
    </details>
  </article>;
}

/** C37 search belongs to word and card candidate routes; the release summaries and the index stay lists. */
export function candidateSearchVisible(routePath: string): boolean {
  return routePath !== 'release' && routePath !== 'compare/release' && routePath !== '';
}

function ReleaseIndexList({ card }: { card: ReleaseIndex }) {
  const collator = new Intl.Collator('uk');
  const listed = new Map(groupReleasePages(card.rows).dispositions.map(item => [item.cardId, item]));
  const items = card.rows.map(row => {
    const entry = readableEntry(row, 1);
    const place = listed.get(row.card_id);
    const pos = entry.facts.find(group => group.field === 'pos')?.facts.map(fact => fact.value).join('; ') || 'not supplied';
    const href = place?.listed && place.key
      ? `${pagePath(place.key)}#entry-${row.card_id}`
      : `/lexicon-v2/release/${encodeURIComponent(row.card_id)}/`;
    return { id: row.card_id, headword: entry.display, pos, status: row.status, href };
  }).sort((a, b) => collator.compare(a.headword, b.headword) || (a.id < b.id ? -1 : 1));
  return <div data-release-index>
    <p data-release-version>Release {card.pin.release_version}</p>
    <p data-release-count>{items.length} cards</p>
    <Scroll label="Every card in this release"><table>
      <caption>Every card in this release</caption>
      <thead><tr><th scope="col">Headword</th><th scope="col">Part of speech</th><th scope="col">Status</th></tr></thead>
      <tbody>{items.map(item => <tr key={item.id} data-index-card={item.id}>
        <th scope="row" lang="uk"><a data-card-page href={item.href}>{item.headword}</a></th>
        <td data-pos={item.pos}>{item.pos}</td>
        <td data-status={item.status}>{item.status}</td>
      </tr>)}</tbody>
    </table></Scroll>
  </div>;
}

export default function WordCardPreview({ card, current, compare }: { card: PreviewCard | ReleaseCard | ReleasePage | ReleaseIndex | LoadedRelease; current: EntryRecord | null; compare: boolean }) {
  if (card.kind === 'release-index') return <ReleaseIndexList card={card} />;
  if (card.kind === 'release') {
    const { pages, dispositions } = groupReleasePages(card.rows);
    const entries = pages.reduce((n, page) => n + page.entries.length, 0);
    return <div data-release-summary>
      <p data-release-version>Release {card.pin.release_version}</p>
      <p data-release-count>{card.rows.length} cards</p>
      <p data-page-count>{pages.length} word pages with {entries} numbered entries. {dispositions.filter(d => !d.listed).length} source cards have no learner page; they stay in the audit details.</p>
      <WithdrawalBanner notice={card.withdrawalNotice} />
      <nav aria-label="Word pages"><ul className="wc-page-list">{pages.map(page => <li key={page.key}>
        <a data-page-link href={pagePath(page.key)}><span lang="uk">{page.title}</span></a>{' '}
        <span>{page.entries.length === 1 ? '1 entry' : `${page.entries.length} entries`}</span>{' '}
        <a data-compare-link href={pagePath(page.key, true)}>Comparison view</a>
      </li>)}</ul></nav>
      <details className="wc-audit" data-release-audit><summary>Sources and audit details</summary>
        <WithdrawalNotice notice={card.withdrawalNotice} />
        <p>Dataset SHA-256: {card.pin.dataset_sha256}. Manifest SHA-256: {card.pin.manifest_sha256}.</p>
        <p>Pages group source cards by exact lowercased spelling. That is page correspondence only, not card identity: no accepted entry-level comparison exists.</p>
        <Accounting rows={card.rows} scope="the whole release" />
        <section aria-label="Manifest filtered assertions"><h3>Manifest filtered assertions</h3>
          <pre data-filtered-assertions>{card.filteredAssertions === undefined ? 'Not declared' : JSON.stringify(card.filteredAssertions, null, 2)}</pre>
          <p>Producer-reported filtering counts, separate from declared gaps and measured absent field classes.</p>
        </section>
        <p data-pairing-count>0/{card.rows.length} paired; {card.rows.length}/{card.rows.length} explicitly unpaired. 0 actual comparisons.</p>
        <p>Data owns the authoritative identity relation; Atlas owns subsequent current-page integration.</p>
        <a href={`https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/new?body=${encodeURIComponent(JSON.stringify(card.pin, null, 2))}`}>Report / improve this release</a>
        <Scroll label="Every source card"><table data-dispositions><caption>Every source card, its page and its raw audit record</caption>
          <thead><tr><th scope="col">Card</th><th scope="col">Kind</th><th scope="col">Status and version</th><th scope="col">Page</th><th scope="col">Entry</th><th scope="col">Disposition</th></tr></thead>
          <tbody>{dispositions.map(d => { const row = card.rows.find(r => r.card_id === d.cardId)!; return <tr key={d.cardId} data-disposition={d.cardId} data-listed={String(d.listed)}>
            <th scope="row"><a data-card-link href={`/lexicon-v2/release/${d.cardId}/`}><code>{d.cardId}</code></a></th><td>{d.cardKind}</td><td>{row.status}, card version {row.card_version}</td>
            <td lang="uk">{d.key ?? '—'}</td><td>{d.ordinal ?? '—'}</td><td>{d.reason}</td>
          </tr>; })}</tbody>
        </table></Scroll>
      </details>
    </div>;
  }
  if (card.kind === 'release-page') return <div data-release-page={card.page.key}>
    <p data-local-artifact-version className="wc-artifact-version">Local candidate renderer v0.1.1</p>
    <p className="wc-page-meta">{card.page.entries.length === 1 ? '1 entry' : `${card.page.entries.length} numbered entries`} · Release {card.pin.release_version}</p>
    <WithdrawalBanner notice={card.withdrawalNotice} />
    {card.page.entries.map(entry => <Entry key={entry.row.card_id} entry={entry} pin={card.pin} />)}
    {compare && <section aria-label="Field comparison"><h2>Field comparison</h2>
      <p>Unresolved pairing. This page groups release cards by exact lowercased spelling; that is page correspondence, not card identity.</p>
      <p>No accepted entry-level comparison exists. 0 actual comparisons. Better/worse unavailable.</p>
    </section>}
    <details className="wc-audit" data-page-audit><summary>Sources and audit details for this page</summary>
      <WithdrawalNotice notice={card.withdrawalNotice} />
      <p>{card.pin.provenance === 'synthetic-fixture' ? 'Synthetic fixture. No linguistic or publication approval.' : 'Producer-declared status. No publication approval is implied.'}</p>
      <PageCredits rows={card.page.entries.map(e => e.row)} pin={card.pin} />
      <p>Dataset SHA-256: {card.pin.dataset_sha256}. Manifest SHA-256: {card.pin.manifest_sha256}.</p>
      <p>Entries share this page because their spelling matches when lowercased. Common entries come first in release order; proper-name entries follow. Each entry keeps its own facts and citations.</p>
      <Accounting rows={card.page.entries.map(e => e.row)} scope="this page" learner />
    </details>
  </div>;
  if (card.kind === 'release-card') {
    const entry = readableEntry(card.row, 1);
    const head = cardHeading(entry);
    const usableIds = usableAssertionIds(card.row);
    const senseLabels = entry.senses.flatMap(s => s.groups.filter(g => g.field === 'sense_label')
      .flatMap(g => g.facts.filter(f => f.assertionIds.some(id => usableIds.has(id))).map(f => f.value)));
    const synthetic = card.pin.provenance === 'synthetic-fixture';
    return <div data-release-card={card.row.card_id}>
      <p className="wc-page-meta">
        <span data-release-version>Release {card.pin.release_version}</span> · <span data-card-version>Card version {card.row.card_version}</span>
      </p>
      {synthetic && <p>Synthetic fixture. CERTIFIED exercises the UI branch under test authority only. No linguistic or publication approval.</p>}
      <WithdrawalBanner notice={card.withdrawalNotice} />
      <article className="wc-entry" data-entry={card.row.card_id} data-entry-kind={card.row.card_kind} aria-labelledby={`entry-${card.row.card_id}`}>
        <h2 id={`entry-${card.row.card_id}`}><span lang={head.hasText ? 'uk' : undefined}>{head.heading}</span></h2>
        <p className="wc-kind" data-entry-label>{KIND_LABELS[card.row.card_kind] ?? card.row.card_kind}
          {entry.proper && <> — {senseLabels.length ? <span lang="uk">{senseLabels.join('; ')}</span> : 'no sense label supplied'}.</>}
          {' '}<span className="wc-status" data-release-status data-entry-status>{card.row.status}</span></p>
        <EntryContent entry={entry} />
      </article>
      {compare && <section aria-label="Field comparison"><h2>Field comparison</h2>
        <p>Unresolved pairing. This release has no assembled-card identity keys. No comparison rows.</p>
        <p>Better/worse unavailable pending independently accepted comparison evidence.</p>
        <p>Data owns the authoritative identity relation; Atlas owns current-page integration. No actual comparison is claimed.</p>
      </section>}
      <details className="wc-audit" data-card-audit={card.row.card_id}><summary>Sources and audit</summary>
        <WithdrawalNotice notice={card.withdrawalNotice} />
        <p>Card <code>{card.row.card_id}</code>, card version <code>{card.row.card_version}</code>, producer status {card.row.status}.</p>
        {!synthetic && <p>Producer-declared status. No publication approval is implied.</p>}
        <PageCredits rows={[card.row]} pin={card.pin} />
        <section aria-label="Known gaps"><h3>Known gaps</h3><p>Declared metadata, not language facts.</p>
          {card.row.known_gaps.length ? card.row.known_gaps.map((gap, i) => <pre key={i}>{typeof gap === 'string' ? gap : JSON.stringify(gap, null, 2)}</pre>) : <p>No declared gaps</p>}
        </section>
        <Accounting rows={[card.row]} scope="this card" />
        <section aria-label="Parallel cited assertions"><h3>Parallel cited assertions</h3>
          <p>Assertions remain separate. No field resolution or semantic verdict is inferred.</p>
          {card.row.fields.map(field => <AssertionRecord key={field.assertion_id} card={card} field={field} />)}
        </section>
      </details>
    </div>;
  }
  if (card.kind === 'unavailable') return <p role="status">Unavailable: {card.reason}</p>;
  if (card.kind === 'suppressed') return <p role="status">Suppressed. No card body.</p>;
  if (card.kind === 'successors') return <section aria-label="Successors"><p>{card.state}</p><ul>{card.ids.map(id => <li key={id}>{id}</li>)}</ul></section>;
  return <div data-preview-card={card.id}>
    <h2>Candidate {card.id}</h2>
    {(['forms', 'stress', 'senses', 'examples', 'citations'] as const).map(group => {
      const fields = group === 'citations' ? card.fields : card.fields.filter(f => f.group === group);
      return <section aria-label={group} key={group}>
        <h3>{group}</h3>
        {fields.length === 0 && <p>Missing source data</p>}
        {fields.map(f => <article key={f.path} data-field={f.path}>
          <h4>{f.path}</h4>
          {group === 'citations' ? (f.citations.length ? f.citations.map(c => <pre key={c.assertion_id}>{JSON.stringify(c, null, 2)}</pre>) : <p>Missing source data</p>) : <>
            <p data-field-state>{f.state}</p>
            {f.refusal && <p>{f.refusal}</p>}
            {f.raw.length ? f.raw.map((v, i) => <pre data-raw-value key={i}>{typeof v === 'string' ? v : JSON.stringify(v, null, 2)}</pre>) : <p>No selected fact. Missing source data.</p>}
            <p>Evidence: {f.citations.map(c => `${c.assertion_id} | ${c.source_id} | ${c.snapshot_id} | ${c.locator}`).join('; ') || 'No displayable selected assertion'}</p>
          </>}
        </article>)}
      </section>;
    })}
    {compare && <section aria-label="Field comparison">
      <h2>Field comparison</h2>
      <p>Better/worse unavailable pending independently accepted comparison evidence.</p>
      {current ? <table><thead><tr><th>Current field</th><th>Current raw value</th><th>Candidate raw value</th><th>Result and evidence</th></tr></thead>
        <tbody>{compareCurrent(current, card).map(row => <tr key={row.path} data-comparison={row.path}>
          <th>{row.path}</th><td><pre>{typeof row.current === 'string' ? row.current : JSON.stringify(row.current, null, 2)}</pre></td>
          <td><pre>{JSON.stringify(row.candidate, null, 2)}</pre></td><td data-result={row.result}>{row.result}<p>{row.evidence}</p></td>
        </tr>)}</tbody></table> : <p>Unresolved pairing. No unique documented current identity key. Current facts remain missing.</p>}
    </section>}
  </div>;
}
