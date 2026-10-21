import { compareCurrent, type PreviewCard } from '../lib/lexicon/word-card-preview';
import type { EntryRecord } from '../lib/lexicon/atlas-data-source';
import { attributionGap, attributionLinks, releaseAccounting, releaseReportUrl, type LoadedRelease, type ReleaseCard } from '../lib/lexicon/word-card-release';

function Accounting({ rows }: Pick<LoadedRelease, 'rows'>) {
  return <section aria-label="Measured release coverage"><h3>Measured release coverage</h3>
    <pre data-release-accounting>{JSON.stringify(releaseAccounting(rows), null, 2)}</pre>
    <p>Absent field classes are measured separately from producer-declared gaps. No declared gaps does not establish completeness.</p>
    <p>Attribution gaps remain owned by Data. Source strings are preserved, including placeholders.</p>
  </section>;
}

export default function WordCardPreview({ card, current, compare }: { card: PreviewCard | ReleaseCard | LoadedRelease; current: EntryRecord | null; compare: boolean }) {
  if (card.kind === 'release') return <div data-release-summary>
    <p data-release-version>Release {card.pin.release_version}</p>
    <p data-release-count>{card.rows.length} cards</p>
    <p>Dataset SHA-256: {card.pin.dataset_sha256}. Manifest SHA-256: {card.pin.manifest_sha256}.</p>
    <Accounting rows={card.rows} />
    <section aria-label="Manifest filtered assertions"><h3>Manifest filtered assertions</h3>
      <pre data-filtered-assertions>{card.filteredAssertions === undefined ? 'Not declared' : JSON.stringify(card.filteredAssertions, null, 2)}</pre>
      <p>Producer-reported filtering counts, separate from declared gaps and measured absent field classes.</p>
    </section>
    <p data-pairing-count>0/{card.rows.length} paired; {card.rows.length}/{card.rows.length} explicitly unpaired. 0 actual comparisons.</p>
    <p>Data owns the authoritative identity relation; Atlas owns subsequent current-page integration. PP-03/PV-02 and section 9 remain open.</p>
    <a href={`https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/new?body=${encodeURIComponent(JSON.stringify(card.pin, null, 2))}`}>Report / improve this release</a>
    <ul>{card.rows.map(row => <li key={row.card_id}>
      <a data-card-link href={`/lexicon-v2/release/${row.card_id}/`}>{row.card_id}</a>{' '}
      <a data-compare-link href={`/lexicon-v2/compare/release/${row.card_id}/`}>Unpaired comparison page</a>{' '}
      {row.status}, card version {row.card_version}
    </li>)}</ul>
    {card.withdrawalNotice !== undefined && <section aria-label="Withdrawal notice"><h3>Withdrawal notice</h3>
      <pre>{JSON.stringify(card.withdrawalNotice, null, 2)}</pre>
    </section>}
  </div>;
  if (card.kind === 'release-card') return <div data-release-card={card.row.card_id}>
    <h2>{card.row.status} {card.row.card_id}</h2>
    <p data-release-version>Release {card.pin.release_version}</p>
    <p data-card-version>Card version {card.row.card_version}</p>
    <p data-release-status>{card.row.status}</p>
    <p>{card.pin.provenance === 'synthetic-fixture' ?
      'Synthetic fixture. CERTIFIED exercises the UI branch under test authority only. No linguistic or publication approval.' :
      'Producer-declared status. No publication approval is implied.'}</p>
    {card.withdrawalNotice !== undefined && <section aria-label="Withdrawal notice"><h3>Withdrawal notice</h3>
      <pre>{JSON.stringify(card.withdrawalNotice, null, 2)}</pre>
    </section>}
    <section aria-label="Known gaps"><h3>Known gaps</h3><p>Declared metadata, not language facts.</p>
      {card.row.known_gaps.length ? card.row.known_gaps.map((gap, i) => <pre key={i}>{typeof gap === 'string' ? gap : JSON.stringify(gap, null, 2)}</pre>) : <p>No declared gaps</p>}
    </section>
    <Accounting rows={[card.row]} />
    <section aria-label="Parallel cited assertions"><h3>Parallel cited assertions</h3>
      <p>Assertions remain separate. No field resolution or semantic verdict is inferred.</p>
      {card.row.fields.map(field => <article key={field.assertion_id} data-release-assertion={field.assertion_id}>
        <h4>{field.field}</h4><p>{field.subject.kind}: {field.subject.id}</p>
        <pre data-raw-value>{typeof field.value === 'string' ? field.value : JSON.stringify(field.value, null, 2)}</pre>
        <pre data-release-citation>{JSON.stringify(field.citation, null, 2)}</pre>
        <p data-source-attribution>{field.citation.attribution}</p>
        {attributionLinks(field.citation.attribution).map(url => <a data-source-link key={url} href={url}>{url}</a>)}
        {attributionGap(field.citation) && <p data-attribution-gap={attributionGap(field.citation)}>Attribution gap: {attributionGap(field.citation)}. Owner Data. Placeholder retained verbatim.</p>}
        <a data-report-action href={releaseReportUrl(card, field)}>Report / improve this assertion</a>
      </article>)}
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
