import { compareCurrent, type PreviewCard } from '../lib/lexicon/word-card-preview';
import type { EntryRecord } from '../lib/lexicon/atlas-data-source';

export default function WordCardPreview({ card, current, compare }: { card: PreviewCard; current: EntryRecord | null; compare: boolean }) {
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
