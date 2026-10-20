import { describe, expect, it } from 'vitest';
import { displayValue, groupReleasePages, pageKey, pagePath, readableEntry, slotLabel, PageKeyError, type ReadableEntry } from '../../src/lib/lexicon/word-card-readable';
import { attributionGap, loadWordCardRelease, type ReleaseRow } from '../../src/lib/lexicon/word-card-release';
import { publicReleasePin } from '../../src/lib/lexicon/word-card-preview-inputs';

type Field = ReleaseRow['fields'][number];
const ULIF = '«Словники України online», https://lcorp.ulif.org.ua/dictua/ (entry reference)';
let next = 0;
function field(cardId: string, name: string, value: Field['value'], source = 'ulif', subject: Field['subject'] = { kind: 'card', id: cardId }): Field {
  const attribution = source === 'ulif' ? ULIF : source === 'puls' ? 'PULS citation above.' : `${source} https://evil.invalid/x`;
  return { assertion_id: `wa_${String(next++).padStart(24, '0')}`, subject, field: name, value, citation: { source_id: source, snapshot_id: 's', locator: `${source}:1`,
    licence_ref: { register_source_id: source, register_version: 1 }, attribution, licence: { name: 'terms' }, terms_ref: 'docs/sources/permissions-register.yaml' } };
}
function row(id: string, kind: string, fields: (cardId: string) => Field[]): ReleaseRow {
  return { card_id: id, card_kind: kind, card_version: `cv_${id}`, status: 'CANDIDATE', known_gaps: [], fields: fields(id) };
}
const word = (id: string, spelling: string, kind = 'lexeme', extra: (cardId: string) => Field[] = () => []) =>
  row(id, kind, c => [field(c, 'spelling', spelling), ...extra(c)]);
const covered = (e: ReadableEntry) => [...e.facts, ...e.other, ...e.senses.flatMap(s => s.groups)].flatMap(g => g.facts.flatMap(f => f.assertionIds))
  .concat(e.paradigms.flatMap(t => t.assertionIds));

describe('page keys', () => {
  it('lowercases the single card-subject spelling, or mwe_form for MWE cards, and preserves case elsewhere', () => {
    expect(pageKey(word('wc_a', 'Батьківщина'))).toBe('батьківщина');
    expect(pageKey(row('wc_b', 'mwe', c => [field(c, 'mwe_form', 'Блигом світ'), field(c, 'spelling', 'інше')]))).toBe('блигом світ');
    expect(pageKey(row('wc_c', 'lexeme', c => [field(c, 'spelling', 'Банк'), field(c, 'spelling', 'банк', 'vesum')]))).toBe('банк');
  });
  it.each([
    ['missing', row('wc_d', 'lexeme', c => [field(c, 'stress', 'ба́нк')])],
    ['ambiguous', row('wc_e', 'lexeme', c => [field(c, 'spelling', 'банк'), field(c, 'spelling', 'бар')])],
    ['non-string', row('wc_f', 'lexeme', c => [field(c, 'spelling', ['банк'])])],
    ['sense subject only', row('wc_g', 'lexeme', c => [field(c, 'spelling', 'банк', 'ulif', { kind: 'sense', id: 'ws_1' })])],
    ['unsafe path', word('wc_h', 'a/b')], ['untrimmed', word('wc_i', ' банк')], ['MWE without form', word('wc_j', 'банк', 'mwe')],
  ])('refuses a %s key instead of guessing', (_name, input) => {
    expect(() => pageKey(input)).toThrow(PageKeyError);
  });
  it('encodes page paths inside the lexicon-v2 boundary', () => {
    expect(pagePath('різати правду-матку')).toBe('/lexicon-v2/word/%D1%80%D1%96%D0%B7%D0%B0%D1%82%D0%B8%20%D0%BF%D1%80%D0%B0%D0%B2%D0%B4%D1%83-%D0%BC%D0%B0%D1%82%D0%BA%D1%83/');
    expect(pagePath('банк', true)).toBe('/lexicon-v2/compare/word/%D0%B1%D0%B0%D0%BD%D0%BA/');
  });
});

describe('grouping', () => {
  const rows = [
    word('wc_p1', 'Банк', 'proper_name'), word('wc_l1', 'банк'), word('wc_l2', 'банк'), word('wc_p2', 'Шуба', 'proper_name'),
    row('wc_bad', 'lexeme', c => [field(c, 'stress', 'x')]), word('wc_b1', 'Батьківщина'), word('wc_b2', 'Батьківщина', 'proper_name'),
    row('wc_m1', 'mwe', c => [field(c, 'mwe_form', 'блигом світ')]),
  ];
  const { pages, dispositions } = groupReleasePages(rows);
  it('keeps homonyms as separate numbered entries, common first in release order and proper names last', () => {
    expect(pages.map(p => [p.key, p.title, p.entries.map(e => [e.ordinal, e.row.card_id, e.proper])])).toEqual([
      ['банк', 'банк', [[1, 'wc_l1', false], [2, 'wc_l2', false], [3, 'wc_p1', true]]],
      ['батьківщина', 'Батьківщина', [[1, 'wc_b1', false], [2, 'wc_b2', true]]],
      ['блигом світ', 'блигом світ', [[1, 'wc_m1', false]]],
    ]);
  });
  it('records every row once, leaving proper-only and keyless rows explicitly unlisted', () => {
    expect(dispositions.map(d => d.cardId)).toEqual(rows.map(r => r.card_id));
    expect(dispositions.filter(d => !d.listed)).toEqual([
      { cardId: 'wc_p2', cardKind: 'proper_name', key: 'шуба', ordinal: null, listed: false, reason: 'Proper name without a common entry on its page' },
      { cardId: 'wc_bad', cardKind: 'lexeme', key: null, ordinal: null, listed: false, reason: 'Missing or ambiguous page key' },
    ]);
  });
  it('rethrows unexpected errors instead of hiding them as refusals', () => {
    const broken = { ...word('wc_x', 'банк'), get fields(): Field[] { throw new TypeError('boom'); } };
    expect(() => groupReleasePages([broken])).toThrow(TypeError);
  });
});

describe('readable entry', () => {
  const entry = readableEntry(row('wc_q', 'lexeme', c => [
    field(c, 'spelling', 'вряди-годи'), field(c, 'spelling', 'вряди-годи', 'vesum'), field(c, 'stress', 'вряди́-годи́'),
    field(c, 'stress', 'вряди́-го́ди', 'ukrainian_word_stress'), field(c, 'pos', 'adv'), field(c, 'cefr', 'B1', 'puls'), field(c, 'gender', ['m', 'f']),
    field(c, 'sense_label', 'час від часу', 'ulif', { kind: 'sense', id: 'ws_1' }),
    field(c, 'synonyms', { group: 'synonyms:1', members: 'ІНОДІ, ЧАСОМ' }, 'ulif', { kind: 'sense', id: 'ws_1' }),
    field(c, 'paradigm', { slot: 'v_rod.p', forms: ['замкі́в'] }), field(c, 'paradigm', { slot: 'v_naz.s', forms: ['за́мок'] }),
    field(c, 'paradigm', { slot: 'v_naz.p', forms: ['замки́', 'за́мки'] }), field(c, 'paradigm', { slot: 'v_naz', forms: ['нові́'] }),
    field(c, 'paradigm', { slot: 'v_naz.s.m', forms: ['нови́й'] }), field(c, 'paradigm', { slot: 'v_xyz.s', forms: ['?'] }),
    field(c, 'paradigm', { slot: 'v_naz.q', forms: ['??'] }), field(c, 'paradigm', { slot: 'past.s.f', forms: ['чита́ла'] }),
    field(c, 'paradigm', { slot: 'inf', forms: ['чита́ти'] }), field(c, 'paradigm', { slot: 'pres.s.1', forms: ['чита́ю'] }),
    field(c, 'paradigm', { slot: 'v_dav.s', forms: ['за́мку'], tags: ['noun'] }, 'vesum'),
    field(c, 'paradigm', { slot: 'v_dav.s', forms: 'not-a-list' }), field(c, 'definition_uk', 'тлумачення'),
    field(c, 'antonyms', 'x', 'ulif', { kind: 'link', id: 'wl_1' }), field('wc_other', 'pos', 'noun'),
  ]), 2);
  it('places every assertion in exactly one readable fact, sense, table or literal fallback', () => {
    expect(covered(entry).sort()).toEqual(entry.row.fields.map(f => f.assertion_id).sort());
  });
  it('keeps conflicting stress parallel with separate credits and falls back to the spelling heading', () => {
    const stress = entry.facts.find(g => g.field === 'stress');
    expect(stress?.facts.map(f => [f.value, f.credits.map(c => c.sourceId)])).toEqual([['вряди́-годи́', ['ulif']], ['вряди́-го́ди', ['ukrainian_word_stress']]]);
    expect([entry.heading, entry.display, entry.ordinal]).toEqual(['вряди-годи', 'вряди-годи', 2]);
    expect(entry.facts.map(g => g.field)).toEqual(['spelling', 'stress', 'pos', 'gender', 'cefr']);
    expect(entry.facts[0]?.facts).toHaveLength(1);
    expect(entry.facts[0]?.facts[0]?.credits.map(c => [c.sourceId, c.href, c.gap])).toEqual([
      ['ulif', 'https://lcorp.ulif.org.ua/dictua/', null], ['vesum', null, null]]);
    expect(entry.facts.find(g => g.field === 'cefr')?.facts[0]?.credits[0]?.gap).toBe('puls_reference_placeholder');
    expect(readableEntry(word('wc_s', 'банк', 'lexeme', c => [field(c, 'stress', 'ба́нк')]), 1).heading).toBe('ба́нк');
  });
  it('renders supplied values literally', () => {
    expect(entry.facts.find(g => g.field === 'gender')?.facts[0]?.value).toBe('m, f');
    expect(entry.senses).toEqual([{ id: 'ws_1', groups: [expect.objectContaining({ field: 'sense_label' }), expect.objectContaining({ field: 'synonyms' })] }]);
    expect(entry.senses[0]?.groups[1]?.facts[0]?.value).toBe('ІНОДІ, ЧАСОМ');
    expect(entry.other.map(g => [g.field, g.facts.map(f => f.value)])).toEqual([
      ['paradigm', ['{"slot":"v_dav.s","forms":"not-a-list"}']], ['definition_uk', ['тлумачення']], ['antonyms', ['x']], ['pos', ['noun']]]);
    expect([displayValue(null), displayValue(3), displayValue([1, 'a']), displayValue({ a: 1 })]).toEqual(['null', '3', '[1,"a"]', '{"a":1}']);
  });
  it('builds per-source case and form tables from known slot codes, keeping unknown codes literal', () => {
    const [ulif, vesum] = entry.paradigms;
    expect(ulif?.columns.map(c => [c.key, c.label.text])).toEqual([['s', 'однина'], ['s.m', 'однина, чол. р.'], ['p', 'множина'], ['', 'Number not given in source']]);
    expect(ulif?.caseRows.map(r => [r.label, r.cells.map(c => c?.forms.join(', ') ?? null)])).toEqual([
      ['Називний', ['за́мок', 'нови́й', 'замки́, за́мки', 'нові́']], ['Родовий', [null, null, 'замкі́в', null]]]);
    expect(ulif?.formRows.map(r => [r.slot, r.label])).toEqual([
      ['inf', { text: 'інфінітив', unknown: false }], ['pres.s.1', { text: 'теперішній час, однина, 1 особа', unknown: false }],
      ['past.s.f', { text: 'минулий час, однина, жін. р.', unknown: false }],
      ['v_xyz.s', { text: 'v_xyz.s', unknown: true }], ['v_naz.q', { text: 'v_naz.q', unknown: true }]]);
    expect(vesum?.caseRows).toEqual([{ label: 'Давальний', cells: [expect.objectContaining({ forms: ['за́мку'] })] }]);
    expect(slotLabel('')).toEqual({ text: '', unknown: false });
  });
  it('keeps an entry without paradigm explicitly empty', () => {
    expect(readableEntry(word('wc_z', 'замок'), 1).paradigms).toEqual([]);
  });
});

// The 13 producer proper-name IDs frozen by the driver (R/234-proper-name-frozen-ids.json).
const PROPER = ['wc_0a3k6ypbjhrf', 'wc_91fq1gtsh9f5', 'wc_anz167as5tn7', 'wc_bz5ypsm3wyj7', 'wc_d2d38y0ctmct', 'wc_fvxestgxf73d', 'wc_gv7g0005qb5d',
  'wc_rk47ephm1bts', 'wc_rq9bnybm7ybm', 'wc_sr1x6gb3wqbs', 'wc_sye0ppkx0dwh', 'wc_tnxmxw3kjras', 'wc_zhvykdar3452'];
// Page key = card IDs in entry order, computed independently from the release bytes; '!' marks an unlisted page.
const FROZEN_PAGES = (
  `бабин=wc_96p4nx83f894,wc_gv7g0005qb5d|бабуся=wc_a4ndp7w0v8dq,wc_anz167as5tn7|базар=wc_pr69ykkbh95m,wc_tnxmxw3kjras|` +
  `бандура=wc_km3asrjbxhjb,wc_rq9bnybm7ybm|банк=wc_xbw7msqev2mz,wc_rk47ephm1bts|бар=wc_wmyzn565rxp4,wc_d2d38y0ctmct|` +
  `баран=wc_02a5cjxcpbcf,wc_0a3k6ypbjhrf|батьківщина=wc_6hg8x80fcnk2,wc_sr1x6gb3wqbs|благородний жест=wc_rmvh0tsz1y1a|` +
  `блекоти наїлась=wc_k1kp85tahqag|блигом світ=wc_5j37jfndz666|близько не пахне=wc_562eqy9g3bck|` +
  `блискавкою прорізати=wc_tm57q9wj8y31|блудний син=wc_wzct64k4fham|бог зна що таке=wc_xmzv71z7hwee|` +
  `бог помилував=wc_fc08gvq844db|боже помагай=wc_bej8fh02sp6p|божий світ=wc_ref9xyps30mx|валаамова ослиця=wc_vzt7m2k3tg48|` +
  `вряди-годи=wc_q97mnya76nx7|гнат-безп'ятко=wc_7a6x6n8rek4y|господь його розбере=wc_p1d31y378qs1|` +
  `замок=wc_bgr5q9c06wxg,wc_cvkw5nzdg00n|ключ=wc_h509ejs613sy,wc_p646xsqq40xt|любов=wc_8z09eyahcs88,wc_fvxestgxf73d|` +
  `мама=wc_ea2fvbcb6p3k,wc_zhvykdar3452|новий=wc_cxjtr6481e7t,wc_91fq1gtsh9f5|помилка=wc_jgravxme007h|` +
  `робінзон на безлюдному острові=wc_c66xvp4hvdev|різати правду-матку=wc_1nrw339ddgvm|` +
  `самий=wc_gbh31d6zptnx,wc_k45tstzkx2b6|число=wc_36p338sk68qm|читати=wc_043h3npd7ed4|чоловік=wc_nhac073v3589|` +
  `чоловічий=wc_8kf3af4b8vth|чому=wc_8mhjfw05sm0t|чорний=wc_jrycyzsy17qk|чорно-білий=wc_jb4p3ppvcyvx|` +
  `чотири=wc_w7tnaqg1amv4|чотириста=wc_qt1ajf0trs35|чотирнадцятий=wc_hmz9x3anb1ma|чотирнадцять=wc_qs3tehs0xz6e|` +
  `чудовий=wc_yd5ekty2j7kb|чути=wc_yh60ravvq5am|шампанське=wc_9zfg3rrkkqzf|шампунь=wc_zc0b8ncwj5b9|шапка=wc_0wv95b3qm707|` +
  `шафа=wc_fd7d7wa6rn62|шафка=wc_c6j1qtrpbcgx|швидка=wc_ppr39m6qsr4e|швидко=wc_0r1cdw5z36cd|швидше=wc_2q1qzzw8gd01|` +
  `шестеро=wc_bfdeknm81e44|ширина=wc_qq67z33prpah|ширший=wc_jm7nfbvag8kp|шкарпетка=wc_cnq7f88k186e|школа=wc_qpcdgkctp7ne|` +
  `школяр=wc_m6bs5ramkdgy|школярка=wc_dstgm8vb5xfr|шкідливий=wc_3rc3vnk4r328|шлюб=wc_9wjbgkp9fak8|шматок=wc_f1m5pppp1619|` +
  `шніцель=wc_xmnw6aata5me|шоколад=wc_b92hz3ncnw1a|шоколадка=wc_yff8w36wws3j|шоколадний=wc_6f8yq9yvp0ns|` +
  `шорти=wc_m141ewnvv2m4|шостий=wc_qm83zt29py0d|шофер=wc_8bbj9gn4qm3z|штамп=wc_y9j49mes11mr|штора=wc_x5v9xqax0t4d|` +
  `штраф=wc_zw0vjc1dxpsf|шуба=wc_bz5ypsm3wyj7!|шукати=wc_r6xe3vt4qtw9|шістдесят=wc_q7x9wprhedkr|` +
  `шістдесятий=wc_k339xj1q2hv7|шістнадцятий=wc_8t60pamgdqs0|шістнадцять=wc_pmenjgpx1mh9|шістсот=wc_f70edzrhfy8e|` +
  `шість=wc_sredngg8tzb0|щасливо=wc_hde0r633f7cq|ще=wc_08svjhdbe0fq|щедрий=wc_raxj8hwpvp62|щедрівка=wc_n1g44brn5vs2|` +
  `щирий=wc_4w8bcapex04x|щиро=wc_rn15mnpkqxar|щовечора=wc_vqtt12t22gam|щовівторка=wc_rezqg70bnyy4|щогодини=wc_j1acg1649rw8|` +
  `щоденний=wc_jq9rtqw9yt7y|щодня=wc_5b36dst0her6|щодо=wc_5s9kgf5brczs|щока=wc_hec14t866f1c|щомісяця=wc_tnwfw0gzfm5q|` +
  `щонеділі=wc_4fm88q03w5qs|щопонеділка=wc_0nq8zajmfvcg|щоразу=wc_tk3jdz1xf0mf|щоранку=wc_btwc6wcf50wv|` +
  `щороку=wc_sfvs2tk37p5y|щорічно=wc_91qt0yt5aqnt|щосереди=wc_rxz969384q84|щосуботи=wc_vm2hbj30pf6c|щось=wc_0c2c6k5nrw0n|` +
  `щотижня=wc_5031n96dwgnt|щохвилини=wc_acq6r56secba|щочетверга=wc_ka0tp1vt39e8|щітка=wc_7vqqh0c120vy|` +
  `ювелірний=wc_w78q6xbserdn|ювілей=wc_yr4ee7vav0mq|юнеско=wc_sye0ppkx0dwh!|юридичний=wc_prfy102qxyrn|` +
  `юристка=wc_tpye2vc45frf|я=wc_h54f47k5py6b|яблуко=wc_p41ag4cb6be8|яблучний=wc_wq7h18tk76dh|ягода=wc_spx94fnzqre4|` +
  `язик=wc_ffw1zgt1exvw|яйце=wc_6bt62wd6zzzf|якби=wc_ht0ejvdkh8qe|який-небудь=wc_grkg2vxacyp0|який=wc_345emw0fe2hr|` +
  `якийсь=wc_7e1t38e50r34|якнайшвидше=wc_e1n2pwrrajma|якщо=wc_da7t5vpprjw3|якісний=wc_vfqatzjagh7j|якість=wc_wst7h8j302z2|` +
  `ялинка=wc_vy1cr9bw4wsq|яловичий=wc_vtqv6my006c3|яловичина=wc_d3qyg6mhjx07|ярмарок=wc_vq34ms5wtfev|` +
  `яскравий=wc_a7k5wtq89cdg|яскравіший=wc_2xzw44zg56aq|ясно=wc_5btr8jkdzvd1|яхта=wc_sj76cz4exr2z|ящик=wc_f0nnsej1zh7n|` +
  `яєчня=wc_vnk3jt6x4cw6`).split('|');

// Actual-release proof is an explicit local configuration; CI controls remain offline.
describe.runIf(process.env.ATLAS_WORD_CARD_PUBLIC_PROOF_PATH)('actual release v0.1.0-pilot', () => {
  // Collected even when skipped, so the release loads only when configured.
  const loaded = process.env.ATLAS_WORD_CARD_PUBLIC_PROOF_PATH ? loadWordCardRelease({ enabled: true, public: true,
    artifactPath: process.env.ATLAS_WORD_CARD_PUBLIC_PROOF_PATH, pin: JSON.stringify(publicReleasePin) }) : null;
  const release = loaded?.kind === 'release' ? loaded : { rows: [] as ReleaseRow[] };
  const { pages, dispositions } = groupReleasePages(release.rows);
  const entries = pages.flatMap(p => p.entries);
  it('loads the pinned bytes', () => expect(loaded?.kind).toBe('release'));
  it('matches every one of the 150 frozen row dispositions and the 134/148 learner denominators', () => {
    expect([release.rows.length, release.rows.reduce((n, r) => n + r.fields.length, 0), FROZEN_PAGES.length]).toEqual([150, 2978, 136]);
    const expected = new Map(FROZEN_PAGES.flatMap(line => { const [key = '', ids = ''] = line.split('=');
      return ids.replace('!', '').split(',').map((id, i) => [id, { key, ordinal: ids.endsWith('!') ? null : i + 1, listed: !ids.endsWith('!') }] as const); }));
    expect(expected.size).toBe(150);
    for (const d of dispositions) expect({ key: d.key, ordinal: d.ordinal, listed: d.listed }, d.cardId).toEqual(expected.get(d.cardId));
    expect([pages.length, entries.length, entries.filter(e => !e.proper).length]).toEqual([134, 148, 137]);
    expect(pages.map(p => p.key)).toEqual(FROZEN_PAGES.filter(l => !l.endsWith('!')).map(l => l.split('=')[0]).sort(new Intl.Collator('uk').compare));
    expect(new Set(entries.map(e => e.row.card_id)).size).toBe(148);
  });
  it('classifies all 13 proper names: 11 last on a common page, 2 unlisted', () => {
    expect(release.rows.filter(r => r.card_kind === 'proper_name').map(r => r.card_id).sort()).toEqual(PROPER);
    for (const id of PROPER) {
      const page = pages.find(p => p.entries.some(e => e.row.card_id === id));
      const d = dispositions.find(x => x.cardId === id);
      if (id === 'wc_bz5ypsm3wyj7' || id === 'wc_sye0ppkx0dwh') { expect(page, id).toBeUndefined(); expect(d?.listed).toBe(false); continue; }
      expect(page?.entries.at(-1)?.row.card_id, id).toBe(id);
      expect(page?.entries.some(e => !e.proper), id).toBe(true);
      expect(page?.entries.findIndex(e => e.proper)).toBe(page?.entries.filter(e => !e.proper).length);
    }
    expect(dispositions.filter(d => !d.listed).map(d => [d.cardId, d.key])).toEqual([['wc_bz5ypsm3wyj7', 'шуба'], ['wc_sye0ppkx0dwh', 'юнеско']]);
  });
  it('keeps every assertion of every entry and source facts unmerged', () => {
    for (const e of entries) expect(covered(e).sort(), e.row.card_id).toEqual(e.row.fields.map(f => f.assertion_id).sort());
    const unlisted = release.rows.filter(r => !entries.some(e => e.row === r));
    expect(entries.reduce((n, e) => n + e.row.fields.length, 0) + unlisted.reduce((n, r) => n + r.fields.length, 0)).toBe(2978);
    const zamok = pages.find(p => p.key === 'замок')?.entries;
    expect(zamok?.map(e => [e.row.card_id, e.heading, e.paradigms.length])).toEqual([['wc_bgr5q9c06wxg', 'замо́к', 0], ['wc_cvkw5nzdg00n', 'за́мок', 1]]);
    const vriady = entries.find(e => e.row.card_id === 'wc_q97mnya76nx7');
    expect(vriady?.facts.find(g => g.field === 'stress')?.facts.map(f => [f.value, f.credits.map(c => c.sourceId).join()]).sort()).toEqual([
      ['вряди́-го́ди', 'ukrainian_word_stress'], ['вряди́-годи́', 'ulif']]);
    // Every fact and table credit surfaces exactly the attribution gaps of the assertions behind it.
    const gaps = { puls_reference_placeholder: 0, vesum_version_placeholder: 0 } as Record<string, number>;
    for (const r of release.rows) {
      const e = readableEntry(r, 1), byId = new Map(r.fields.map(f => [f.assertion_id, attributionGap(f.citation)]));
      for (const unit of [...[...e.facts, ...e.other, ...e.senses.flatMap(s => s.groups)].flatMap(g => g.facts), ...e.paradigms]) {
        const own = unit.assertionIds.map(id => byId.get(id)).filter((gap): gap is string => gap !== null && gap !== undefined);
        expect(new Set(unit.credits.flatMap(c => c.gap ? [c.gap] : [])), r.card_id).toEqual(new Set(own));
        for (const gap of own) gaps[gap] = (gaps[gap] ?? 0) + 1;
      }
    }
    expect(gaps).toEqual({ puls_reference_placeholder: 105, vesum_version_placeholder: 977 });
    expect(entries.flatMap(e => e.paradigms).flatMap(t => t.formRows).filter(r => r.label.unknown)).toEqual([]);
  });
});
