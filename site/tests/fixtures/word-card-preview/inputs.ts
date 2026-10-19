import { readFileSync, readdirSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { resolve } from 'node:path';
import snapshot from './current';

export function record(value: unknown): Record<string, unknown> {
  const isRecord = (v: unknown): v is Record<string, unknown> => v !== null && typeof v === 'object' && !Array.isArray(v);
  if (!isRecord(value)) throw Error('Expected control object');
  return value;
}
function array(value: unknown): unknown[] {
  if (!Array.isArray(value)) throw Error('Expected control array');
  return value;
}
export const hash = (bytes: string | Buffer) => createHash('sha256').update(bytes).digest('hex');
export function loadCases() {
  const root = resolve(process.cwd(), '../docs/atlas/word-cards/examples');
  const originals = readdirSync(root).filter(n => n.endsWith('.json')).sort().map(name => {
    const bytes = readFileSync(resolve(root, name));
    const input: unknown = JSON.parse(bytes.toString());
    return { name: name.slice(0, -5), input, source: `docs/atlas/word-cards/examples/${name}`, sourceHash: hash(bytes), mutations: new Array<string>() };
  });
  const base = originals.find(c => c.name === 'zamok-castle');
  if (!base) throw Error('Missing canonical control source');
  const mutate = (name: string, paths: string[], edit: (card: Record<string, unknown>) => void) => {
    const input = record(structuredClone(base.input));
    edit(input);
    return { ...base, name, input, mutations: paths };
  };
  const stress = (card: Record<string, unknown>) => record(record(card.fields).stress);
  const selectedAssertion = (card: Record<string, unknown>) => {
    const id = stress(card).selected;
    return record(array(card.assertions).find(a => record(a).assertion_id === id));
  };
  function ascii(value: unknown): unknown {
    if (typeof value === 'string') return /[^\x00-\x7f]/.test(value) ? 'CONTROL' : value;
    if (Array.isArray(value)) return value.map(ascii);
    if (value && typeof value === 'object') return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, ascii(v)]));
    return value;
  }
  const complete = mutate('control-complete', ['all non-ASCII strings', 'identity.source_keys=[]', 'all assertion values/value_norm/review', 'all field evidence unverified', 'senses[0].fields.examples', 'assertions + examples'], card => {
    Object.assign(card, record(ascii(card)));
    record(card.identity).source_keys = [];
    function placeholder(value: unknown): unknown {
      if (typeof value === 'string') return 'CONTROL_RAW';
      if (Array.isArray(value)) return value.map(placeholder);
      if (value && typeof value === 'object') return Object.fromEntries(Object.entries(value).map(([k,v]) => [k,placeholder(v)]));
      return value;
    }
    for (const item of array(card.assertions)) {
      const a = record(item); a.value = placeholder(a.value); a.value_norm = 'CONTROL_NORM'; a.review = {status:'none'};
    }
    for (const container of [card.fields, ...array(card.senses).map(s => record(s).fields)]) for (const item of Object.values(record(container))) {
      const r = record(item); r.state = 'unverified'; r.mapping_evidenced = false; r.independence_groups_evidenced = 0;
      for (const value of array(r.values)) Object.assign(record(value), {value_norm:'CONTROL_NORM',mapping_evidenced:false,independence_groups_evidenced:0});
      if (r.propositions) for (const p of Object.values(record(r.propositions))) Object.assign(record(p), {state:'unverified',mapping_evidenced:false,independence_groups_evidenced:0});
    }
    const senses = array(card.senses); const sense = record(senses[0]);
    const fields = record(sense.fields); const definition = record(fields.definition_uk);
    const source = array(card.assertions).find(a => record(a).assertion_id === definition.selected);
    const example = { ...record(structuredClone(source)), assertion_id: 'wa_aaaaaaaaaaaaaaaaaaaaaaaa', field: 'examples', value: 'EXAMPLE_RAW', value_norm: 'example_raw' };
    array(card.assertions).push(example);
    fields.examples = { state: 'single-source', selected: example.assertion_id, values: [{ value_norm: example.value_norm, assertion_ids: [example.assertion_id], independence_groups: [], mapping_evidenced: true, independence_groups_evidenced: 0 }], comparison: 'text', mapping_evidenced: true };
  });
  const controls = [complete,
    mutate('control-conflict', ['fields.stress.state', 'fields.stress.selected'], c => Object.assign(stress(c), { state: 'conflict', selected: null })),
    mutate('control-unverified', ['fields.stress.state'], c => { stress(c).state = 'unverified'; }),
    mutate('control-missing', ['fields.stress'], c => { delete record(c.fields).stress; }),
    mutate('control-suppressed', ['state'], c => { c.state = 'suppressed'; }),
    mutate('control-redirected', ['state', 'merged_into'], c => { c.state = 'redirected'; c.merged_into = 'wc_aaaaaaaaaaaa'; }),
    mutate('control-malformed', ['fields.stress.state'], c => { stress(c).state = 'certified'; }),
    mutate('control-mismatched', ['assertions[selected stress].subject.id'], c => { record(selectedAssertion(c).subject).id = 'wc_stale'; }),
    mutate('control-internal', ['assertions[selected stress].licence_ref.appears_in'], c => { record(selectedAssertion(c).licence_ref).appears_in = ['internal']; }),
    mutate('control-sum11', ['assertions[selected stress].source_id', 'licence_ref.register_source_id'], c => { const a = selectedAssertion(c); a.source_id = 'sum11'; record(a.licence_ref).register_source_id = 'sum11'; }),
    mutate('control-untrusted', ['assertions[selected stress].value'], c => { selectedAssertion(c).value = '<script>globalThis.previewInjected=1</script> RAW  A'; }),
  ];
  return [...originals, ...controls].map(c => ({ ...c, fingerprint: hash(JSON.stringify(c.input)) }));
}
export async function previewInputs() {
  const {pairCurrent, previewCard} = await import('../../../src/lib/lexicon/word-card-preview');
  const cases = loadCases();
  const canonical = cases.filter(c => !c.mutations.length).map(c => c.input);
  const snapshotHash = hash(readFileSync(resolve(process.cwd(), 'tests/fixtures/word-card-preview/current.ts')));
  const common = { generatedAt: snapshot.generatedAt, manifestVersion: snapshot.manifestVersion };
  return [...[...cases.map(c => ({...c, claimants:canonical})), ...revisionCases()].map(c => {
    const card = previewCard(c.input, 'controlled');
    const current = pairCurrent(card, c.claimants.map(input => previewCard(input, 'controlled')), snapshot.records.map(r => r.record));
    return { ...common, ...c, card, current, snapshotHash };
  }), { ...common, name: 'real-data', card: previewCard(null), current: null, source: 'No certified export', fingerprint: hash('real-data-unavailable'), snapshotHash }];
}

export function revisionCases() {
  const originals = loadCases().filter(c => !c.mutations.length);
  const castle = originals.find(c => c.name === 'zamok-castle');
  const predecessor = originals.find(c => c.name === 'zamok-legacy-split');
  if (!castle || !predecessor) throw Error('Missing identity controls');
  const identity = ['suppressed', 'malformed', 'unreadable', 'bad-key'].flatMap(state => {
    const input = record(structuredClone(predecessor.input));
    if (state === 'suppressed') input.state = 'suppressed';
    if (state === 'malformed') input.split_into = array(input.split_into).slice(0,1);
    if (state === 'unreadable') delete input.identity;
    if (state === 'bad-key') record(input.identity).source_keys = [null];
    const claimants = originals.map(c => c === predecessor ? input : c.input);
    return [{...castle, name:`f1-${state}-castle`}, {...predecessor, name:`f1-${state}-predecessor`, input}].map(c =>
      ({...c, claimants, mutations:[`predecessor:${state}`], fingerprint:hash(JSON.stringify({value:c.input,claimants}))}));
  });
  const visibility = ['ubertext_freq','ulp_private','zno_nmt','pohribnyi_1992','ulif'].flatMap(id => ['source','register'].map(binding => {
    const input = record(structuredClone(castle.input));
    const a = record(array(input.assertions).find(a => record(a).assertion_id === record(record(input.fields).stress).selected));
    delete record(a.licence_ref).appears_in;
    if (binding === 'source') a.source_id = id;
    else record(a.licence_ref).register_source_id = id;
    return {...castle, name:`f2-${id}-${binding}`, input, claimants:originals.map(c => c.input), mutations:[`stress.${binding}=${id}`, 'delete appears_in'], fingerprint:hash(JSON.stringify(input))};
  }));
  return [...identity, ...visibility];
}
