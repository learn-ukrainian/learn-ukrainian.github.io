import type { ReactNode } from 'react';
import { compareCurrent, type PreviewCard } from '../lib/lexicon/word-card-preview';
import type { EntryRecord } from '../lib/lexicon/atlas-data-source';
import { attributionGap, attributionLinks, releaseAccounting, releaseReportUrl, type LoadedRelease, type ReleaseCard, type ReleaseRow } from '../lib/lexicon/word-card-release';
import { groupReleasePages, pagePath, type Credit, type FactGroup, type ParadigmCell, type ParadigmTable, type ReadableEntry, type ReleasePage, type SlotLabel } from '../lib/lexicon/word-card-readable';

function Accounting({ rows, scope }: Pick<LoadedRelease, 'rows'> & { scope: string }) {
  return <section aria-label={`Measured coverage of ${scope}`}><h3>Measured coverage of {scope}</h3>
    <pre data-release-accounting>{JSON.stringify(releaseAccounting(rows), null, 2)}</pre>
    <p>Absent field classes are measured separately from producer-declared gaps. No declared gaps does not establish completeness.</p>
    <p>Attribution gaps remain owned by Data. Source strings are preserved, including placeholders.</p>
  </section>;
}

function WithdrawalNotice({ notice }: { notice: LoadedRelease['withdrawalNotice'] }) {
  return notice === undefined ? null : <section aria-label="Withdrawal notice"><h3>Withdrawal notice</h3>
    <pre>{JSON.stringify(notice, null, 2)}</pre>
  </section>;
}

function AssertionRecord({ card, field }: { card: ReleaseCard; field: ReleaseRow['fields'][number] }) {
  return <article data-release-assertion={field.assertion_id}>
    <h4>{field.field}</h4><p>{field.subject.kind}: {field.subject.id}</p>
    <pre data-raw-value>{typeof field.value === 'string' ? field.value : JSON.stringify(field.value, null, 2)}</pre>
    <pre data-release-citation>{JSON.stringify(field.citation, null, 2)}</pre>
    <p data-source-attribution>{field.citation.attribution}</p>
    {attributionLinks(field.citation.attribution).map(url => <a data-source-link key={url} href={url}>{url}</a>)}
    {attributionGap(field.citation) && <p data-attribution-gap={attributionGap(field.citation)}>Attribution gap: {attributionGap(field.citation)}. Owner Data. Placeholder retained verbatim.</p>}
    <a data-report-action href={releaseReportUrl(card, field)}>Report / improve this assertion</a>
  </article>;
}

const FIELD_LABELS: Record<string, string> = { spelling: 'Spelling', mwe_form: 'Expression', stress: 'Stress', pos: 'Part of speech',
  gender: 'Gender', aspect: 'Aspect', grammatical_label: 'Grammar', cefr: 'CEFR level', sense_label: 'Sense', synonyms: 'Synonyms', antonyms: 'Antonyms' };
const UKRAINIAN_FIELDS = new Set(['spelling', 'mwe_form', 'stress', 'grammatical_label', 'sense_label', 'synonyms', 'antonyms']);
const KIND_LABELS: Record<string, string> = { lexeme: 'Word', mwe: 'Multi-word expression', proper_name: 'Proper name' };
const capital = (text: string) => text.charAt(0).toUpperCase() + text.slice(1);

function Credits({ credits }: { credits: Credit[] }) {
  return <span className="wc-credits" data-credits>Source:{credits.map((c, i) => <span key={i}> {c.href ?
    <a data-credit-link href={c.href} title={c.attribution}>{c.sourceId}</a> : <span title={c.attribution}>{c.sourceId}</span>}
    {c.gap && <span data-credit-gap={c.gap}> (attribution incomplete)</span>}</span>)}</span>;
}

function Facts({ groups }: { groups: FactGroup[] }) {
  return <dl className="wc-facts">{groups.map(group => <div key={group.field} data-fact={group.field}>
    <dt>{FIELD_LABELS[group.field] ?? group.field}</dt>
    {group.facts.map((fact, i) => <dd key={i} data-assertions={fact.assertionIds.join(' ')}>
      <span data-fact-value lang={UKRAINIAN_FIELDS.has(group.field) ? 'uk' : undefined}>{fact.value}</span> <Credits credits={fact.credits} />
    </dd>)}
    {group.facts.length > 1 && <dd className="wc-note" data-sources-differ>Sources differ. Each value is shown with its own source; no value is chosen.</dd>}
  </div>)}</dl>;
}

function Label({ label }: { label: SlotLabel }) {
  return label.unknown ? <><code>{label.text}</code> (unrecognised slot code, shown literally)</> : <span lang="uk">{capital(label.text)}</span>;
}

function Cell({ cell }: { cell: ParadigmCell | null }) {
  return cell ? <td lang="uk" data-assertions={cell.assertionIds.join(' ')}>{cell.forms.join(', ')}</td> :
    <td><span aria-hidden="true">—</span><span className="wc-sr-only">not supplied</span></td>;
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

function Entry({ entry, pin }: { entry: ReadableEntry; pin: ReleasePage['pin'] }) {
  const { row, ordinal } = entry;
  const senseLabels = entry.senses.flatMap(s => s.groups.filter(g => g.field === 'sense_label').flatMap(g => g.facts.map(f => f.value)));
  return <article className="wc-entry" data-entry={row.card_id} data-entry-kind={row.card_kind} aria-labelledby={`entry-${row.card_id}`}>
    <h2 id={`entry-${row.card_id}`}><span className="wc-ordinal">{ordinal}.</span> <span lang="uk">{entry.heading}</span></h2>
    <p className="wc-kind" data-entry-label>{KIND_LABELS[row.card_kind] ?? row.card_kind}
      {entry.proper && <> — {senseLabels.length ? <span lang="uk">{senseLabels.join('; ')}</span> : 'no sense label supplied'}. Listed after common entries.</>}
      {' '}<span className="wc-status" data-entry-status>{row.status}</span></p>
    <Facts groups={entry.facts} />
    {entry.senses.length > 0 && <section aria-label={`Senses of entry ${ordinal}`}><h3>Senses</h3>
      <ol className="wc-senses">{entry.senses.map(sense => <li key={sense.id} data-sense={sense.id}><Facts groups={sense.groups} /></li>)}</ol>
    </section>}
    <section aria-label={`Forms of entry ${ordinal}`}><h3>Forms</h3>
      {entry.paradigms.length ? entry.paradigms.map(t => <Paradigm key={t.sourceId} table={t} />) :
        <p data-missing-paradigm>No paradigm is supplied for this entry in this release. Forms are not borrowed from other entries.</p>}
    </section>
    {entry.other.length > 0 && <section aria-label={`Other source facts of entry ${ordinal}`}><h3>Other source facts</h3>
      <p>Shown literally. This preview has no readable layout for these fields yet.</p><Facts groups={entry.other} />
    </section>}
    <details className="wc-audit" data-entry-audit={row.card_id}><summary>Sources and audit details for entry {ordinal}</summary>
      <p>Card <code>{row.card_id}</code>, card version <code data-card-version>{row.card_version}</code>, producer status {row.status}.</p>
      <section aria-label={`Known gaps of entry ${ordinal}`}><h3>Known gaps</h3><p>Declared metadata, not language facts.</p>
        {row.known_gaps.length ? row.known_gaps.map((gap, i) => <pre key={i}>{typeof gap === 'string' ? gap : JSON.stringify(gap, null, 2)}</pre>) : <p>No declared gaps</p>}
      </section>
      <Accounting rows={[row]} scope="this entry" />
      <h3>Cited assertions</h3><p>Assertions remain separate. No field resolution or semantic verdict is inferred.</p>
      {row.fields.map(field => <AssertionRecord key={field.assertion_id} card={{ kind: 'release-card', row, pin }} field={field} />)}
    </details>
  </article>;
}

export default function WordCardPreview({ card, current, compare }: { card: PreviewCard | ReleaseCard | ReleasePage | LoadedRelease; current: EntryRecord | null; compare: boolean }) {
  if (card.kind === 'release') {
    const { pages, dispositions } = groupReleasePages(card.rows);
    const entries = pages.reduce((n, page) => n + page.entries.length, 0);
    return <div data-release-summary>
      <p data-release-version>Release {card.pin.release_version}</p>
      <p data-release-count>{card.rows.length} cards</p>
      <p data-page-count>{pages.length} word pages with {entries} numbered entries. {dispositions.filter(d => !d.listed).length} source cards have no learner page; they stay in the audit details.</p>
      <WithdrawalNotice notice={card.withdrawalNotice} />
      <nav aria-label="Word pages"><ul className="wc-page-list">{pages.map(page => <li key={page.key}>
        <a data-page-link href={pagePath(page.key)}><span lang="uk">{page.title}</span></a>{' '}
        <span>{page.entries.length === 1 ? '1 entry' : `${page.entries.length} entries`}</span>{' '}
        <a data-compare-link href={pagePath(page.key, true)}>Comparison view</a>
      </li>)}</ul></nav>
      <details className="wc-audit" data-release-audit><summary>Sources and audit details</summary>
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
    <p className="wc-page-meta">{card.page.entries.length === 1 ? '1 entry' : `${card.page.entries.length} numbered entries`} · Release {card.pin.release_version}</p>
    <WithdrawalNotice notice={card.withdrawalNotice} />
    {card.page.entries.map(entry => <Entry key={entry.row.card_id} entry={entry} pin={card.pin} />)}
    {compare && <section aria-label="Field comparison"><h2>Field comparison</h2>
      <p>Unresolved pairing. This page groups release cards by exact lowercased spelling; that is page correspondence, not card identity.</p>
      <p>No accepted entry-level comparison exists. 0 actual comparisons. Better/worse unavailable.</p>
    </section>}
    <details className="wc-audit" data-page-audit><summary>Sources and audit details for this page</summary>
      <p>{card.pin.provenance === 'synthetic-fixture' ? 'Synthetic fixture. No linguistic or publication approval.' : 'Producer-declared status. No publication approval is implied.'}</p>
      <p>Dataset SHA-256: {card.pin.dataset_sha256}. Manifest SHA-256: {card.pin.manifest_sha256}.</p>
      <p>Entries share this page because their spelling matches when lowercased. Common entries come first in release order; proper-name entries follow. Each entry keeps its own facts and citations.</p>
      <Accounting rows={card.page.entries.map(e => e.row)} scope="this page" />
    </details>
  </div>;
  if (card.kind === 'release-card') return <div data-release-card={card.row.card_id}>
    <h2>{card.row.status} {card.row.card_id}</h2>
    <p data-release-version>Release {card.pin.release_version}</p>
    <p data-card-version>Card version {card.row.card_version}</p>
    <p data-release-status>{card.row.status}</p>
    <p>{card.pin.provenance === 'synthetic-fixture' ?
      'Synthetic fixture. CERTIFIED exercises the UI branch under test authority only. No linguistic or publication approval.' :
      'Producer-declared status. No publication approval is implied.'}</p>
    <WithdrawalNotice notice={card.withdrawalNotice} />
    <section aria-label="Known gaps"><h3>Known gaps</h3><p>Declared metadata, not language facts.</p>
      {card.row.known_gaps.length ? card.row.known_gaps.map((gap, i) => <pre key={i}>{typeof gap === 'string' ? gap : JSON.stringify(gap, null, 2)}</pre>) : <p>No declared gaps</p>}
    </section>
    <Accounting rows={[card.row]} scope="this card" />
    <section aria-label="Parallel cited assertions"><h3>Parallel cited assertions</h3>
      <p>Assertions remain separate. No field resolution or semantic verdict is inferred.</p>
      {card.row.fields.map(field => <AssertionRecord key={field.assertion_id} card={card} field={field} />)}
    </section>
    {compare && <section aria-label="Field comparison"><h2>Field comparison</h2>
      <p>Unresolved pairing. This release has no assembled-card identity keys. No comparison rows.</p>
      <p>Better/worse unavailable pending independently accepted comparison evidence.</p>
      <p>Data owns the authoritative identity relation; Atlas owns current-page integration. No actual comparison is claimed.</p>
    </section>}
  </div>;
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
