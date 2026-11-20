import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import WordCardPreview, { cardHeading } from '../../src/lexicon/WordCardPreview';
import { groupReleasePages, readableEntry, type ReleasePage } from '../../src/lib/lexicon/word-card-readable';
import { loadWordCardRelease, type ReleaseCard, type ReleaseRow } from '../../src/lib/lexicon/word-card-release';
import { publicReleasePin } from '../../src/lib/lexicon/word-card-preview-inputs';

const pin = {
  release_version: 'v-test',
  provenance: 'producer-declared',
  dataset_sha256: 'a'.repeat(64),
  manifest_sha256: 'b'.repeat(64),
} as const;

let seq = 0;
function mkField(
  cardId: string,
  field: string,
  value: ReleaseRow['fields'][number]['value'],
  source = 'ulif',
  subject: ReleaseRow['fields'][number]['subject'] = { kind: 'card', id: cardId },
): ReleaseRow['fields'][number] {
  const attribution = source === 'ulif'
    ? 'ULIF https://lcorp.ulif.org.ua/dictua/'
    : source === 'vesum'
      ? 'VESUM <used version> https://vesum.nlp.net.ua/'
      : source === 'puls'
        ? 'PULS citation above.'
        : `${source} https://evil.invalid/`;
  return {
    assertion_id: `wa_${String(seq++).padStart(24, '0')}`,
    subject,
    field,
    value,
    citation: {
      source_id: source,
      snapshot_id: 's1',
      locator: `${source}:1`,
      licence_ref: { register_source_id: source, register_version: 1 },
      licence: { name: 'terms' },
      terms_ref: 'docs/sources/permissions-register.yaml',
      attribution,
    },
  };
}

function parseDom(html: string): HTMLDivElement {
  const root = document.createElement('div');
  root.innerHTML = html;
  return root;
}

describe('readable candidate word cards and missing-field visibility', () => {
  it('renders single-card release-card routes headword-first with collapsed Sources and audit', () => {
    // Regression: proper-only cards (e.g. ЮНЕСКО) only exist at /lexicon-v2/release/<id>/ and must not lead with raw JSON.
    const row: ReleaseRow = {
      card_id: 'wc_sye0ppkx0dwh',
      card_kind: 'proper_name',
      card_version: 'cv_test1',
      status: 'CANDIDATE',
      known_gaps: [],
      fields: [
        mkField('wc_sye0ppkx0dwh', 'spelling', 'ЮНЕСКО', 'ulif'),
        mkField('wc_sye0ppkx0dwh', 'stress', 'ЮНЕ́СКО', 'ulif'),
        mkField('wc_sye0ppkx0dwh', 'grammatical_label', 'абревіатура', 'ulif'),
        mkField('wc_sye0ppkx0dwh', 'cefr', 'B1', 'puls'),
      ],
    };
    const card: ReleaseCard = { kind: 'release-card', row, pin };
    const dom = parseDom(renderToStaticMarkup(<WordCardPreview card={card} current={null} compare={false} />));

    expect(dom.querySelector('[data-entry="wc_sye0ppkx0dwh"] h2')?.textContent).toBe('ЮНЕ́СКО');
    expect(dom.querySelector('[data-release-status]')?.textContent).toBe('CANDIDATE');
    expect(dom.querySelector('[data-fact="cefr"] .wc-cefr-badge')?.textContent).toBe('B1');
    expect(dom.querySelector('[data-missing-field="pos"]')?.textContent).toContain('Missing');
    expect(dom.querySelector('[data-missing-field="sense_label"]')?.textContent).toContain('Missing');
    expect(dom.querySelector('[data-missing-field="definition_uk"]')?.textContent).toContain('Missing');
    expect(dom.querySelector('[data-missing-paradigm]')?.textContent).toContain('No paradigm is supplied');

    // No raw JSON <pre> precedes or sits outside the collapsed Sources and audit disclosure.
    expect(Array.from(dom.querySelectorAll('pre')).filter(pre => !pre.closest('details'))).toEqual([]);
    const audit = dom.querySelector('details[data-card-audit="wc_sye0ppkx0dwh"]');
    expect(audit).not.toBeNull();
    expect(audit?.hasAttribute('open')).toBe(false);
    expect(audit?.querySelector(':scope > summary')?.textContent).toBe('Sources and audit');
    expect(audit?.querySelector('[data-release-accounting]')).not.toBeNull();
    expect(audit?.querySelectorAll('[data-release-assertion]')).toHaveLength(4);
    expect(audit?.querySelector('[data-attribution-gap="puls_reference_placeholder"]')).not.toBeNull();
    // Every inline credit marker links to a matching source credit inside the audit details.
    expect(Array.from(dom.querySelectorAll('[data-credit-ref]')).every(a => dom.querySelector(a.getAttribute('href') ?? '') !== null)).toBe(true);
  });

  it('shows missing gender on nouns and missing aspect on verbs, without false missing fields on adverbs', () => {
    const nounNoGender: ReleaseRow = {
      card_id: 'wc_noun00000001',
      card_kind: 'lexeme',
      card_version: 'cv_1',
      status: 'CANDIDATE',
      known_gaps: [],
      fields: [
        mkField('wc_noun00000001', 'spelling', 'шорти'),
        mkField('wc_noun00000001', 'stress', 'шо́рти'),
        mkField('wc_noun00000001', 'pos', 'noun'),
      ],
    };
    const verbNoAspect: ReleaseRow = {
      card_id: 'wc_verb00000001',
      card_kind: 'lexeme',
      card_version: 'cv_2',
      status: 'CANDIDATE',
      known_gaps: [],
      fields: [
        mkField('wc_verb00000001', 'spelling', 'читати'),
        mkField('wc_verb00000001', 'stress', 'чита́ти'),
        mkField('wc_verb00000001', 'pos', 'verb'),
        mkField('wc_verb00000001', 'cefr', 'A1', 'puls'),
      ],
    };
    const adv: ReleaseRow = {
      card_id: 'wc_adv000000001',
      card_kind: 'lexeme',
      card_version: 'cv_3',
      status: 'CANDIDATE',
      known_gaps: [],
      fields: [
        mkField('wc_adv000000001', 'spelling', 'швидко'),
        mkField('wc_adv000000001', 'stress', 'шви́дко'),
        mkField('wc_adv000000001', 'pos', 'adv'),
        mkField('wc_adv000000001', 'cefr', 'A1', 'puls'),
      ],
    };

    const nounDom = parseDom(renderToStaticMarkup(<WordCardPreview card={{ kind: 'release-card', row: nounNoGender, pin }} current={null} compare={false} />));
    expect(nounDom.querySelector('[data-missing-field="gender"]')).not.toBeNull();
    expect(nounDom.querySelector('[data-missing-field="aspect"]')).toBeNull();
    expect(nounDom.querySelector('[data-missing-field="cefr"]')).not.toBeNull();

    const verbDom = parseDom(renderToStaticMarkup(<WordCardPreview card={{ kind: 'release-card', row: verbNoAspect, pin }} current={null} compare={false} />));
    expect(verbDom.querySelector('[data-missing-field="aspect"]')).not.toBeNull();
    expect(verbDom.querySelector('[data-missing-field="gender"]')).toBeNull();
    expect(verbDom.querySelector('[data-missing-field="cefr"]')).toBeNull();

    const advDom = parseDom(renderToStaticMarkup(<WordCardPreview card={{ kind: 'release-card', row: adv, pin }} current={null} compare={false} />));
    expect(advDom.querySelector('[data-missing-field="gender"]')).toBeNull();
    expect(advDom.querySelector('[data-missing-field="aspect"]')).toBeNull();
    expect(advDom.querySelector('[data-missing-field="cefr"]')).toBeNull();

    // F6: array-valued POS such as ["noun", "verb"] stays usable and triggers both noun/verb gap checks.
    const multiPos: ReleaseRow = {
      card_id: 'wc_mpos0000001',
      card_kind: 'lexeme',
      card_version: 'cv_4',
      status: 'CANDIDATE',
      known_gaps: [],
      fields: [
        mkField('wc_mpos0000001', 'spelling', 'мати'),
        mkField('wc_mpos0000001', 'stress', 'ма́ти'),
        mkField('wc_mpos0000001', 'pos', ['noun', 'verb']),
      ],
    };
    const multiPosDom = parseDom(renderToStaticMarkup(<WordCardPreview card={{ kind: 'release-card', row: multiPos, pin }} current={null} compare={false} />));
    expect(multiPosDom.querySelector('[data-fact="pos"] [data-fact-value]')?.textContent).toBe('noun, verb');
    expect(multiPosDom.querySelector('[data-missing-field="pos"]')).toBeNull();
    expect(multiPosDom.querySelector('[data-missing-field="gender"]')).not.toBeNull();
    expect(multiPosDom.querySelector('[data-missing-field="aspect"]')).not.toBeNull();
  });

  it('renders definition_uk with source-neutral Meaning label, Ukrainian lang and actual source credits', () => {
    const row: ReleaseRow = {
      card_id: 'wc_def000000001',
      card_kind: 'lexeme',
      card_version: 'cv_def',
      status: 'CANDIDATE',
      known_gaps: [],
      fields: [
        mkField('wc_def000000001', 'spelling', 'ключ'),
        mkField('wc_def000000001', 'stress', 'ключ'),
        mkField('wc_def000000001', 'pos', 'noun'),
        mkField('wc_def000000001', 'gender', ['m']),
        mkField('wc_def000000001', 'sense_label', 'джерело', 'ulif', { kind: 'sense', id: 'ws_1' }),
        mkField('wc_def000000001', 'definition_uk', 'Водне джерело, що б’є із землі.', 'sum20', { kind: 'sense', id: 'ws_1' }),
        mkField('wc_def000000001', 'definition_uk', 'Потік води з-під землі.', 'vts', { kind: 'sense', id: 'ws_1' }),
      ],
    };
    const page = groupReleasePages([row]).pages[0]!;
    const card: ReleasePage = { kind: 'release-page', page, pin };
    const dom = parseDom(renderToStaticMarkup(<WordCardPreview card={card} current={null} compare={false} />));

    const defGroup = dom.querySelector('[data-sense="ws_1"] [data-fact="definition_uk"]');
    expect(defGroup).not.toBeNull();
    // F1: source-neutral label; actual provenance stays on each citation credit.
    expect(defGroup?.querySelector('dt')?.textContent).toBe('Meaning');
    expect(dom.textContent).not.toContain('ВТС/СУМ-20');
    expect(Array.from(defGroup?.querySelectorAll('[data-fact-value]') ?? []).map(el => [el.getAttribute('lang'), el.textContent])).toEqual([
      ['uk', 'Водне джерело, що б’є із землі.'],
      ['uk', 'Потік води з-під землі.'],
    ]);
    expect(Array.from(defGroup?.querySelectorAll('[data-credit-ref]') ?? []).map(el => el.textContent)).toEqual(['sum20', 'vts']);
    expect(defGroup?.querySelector('[data-sources-differ]')).not.toBeNull();
    expect(dom.querySelector('[data-missing-field="definition_uk"]')).toBeNull();
    expect(dom.querySelector('[data-missing-field="sense_label"]')).toBeNull();
    expect(dom.querySelector('[aria-label^="Other source facts"]')).toBeNull();
  });

  it('shows competing spellings or MWE forms together instead of picking by assertion order (F2)', () => {
    const competingSpelling: ReleaseRow = {
      card_id: 'wc_amb000000001',
      card_kind: 'lexeme',
      card_version: 'cv_amb',
      status: 'CANDIDATE',
      known_gaps: [],
      fields: [
        mkField('wc_amb000000001', 'spelling', 'варіант1', 'ulif'),
        mkField('wc_amb000000001', 'spelling', 'варіант2', 'vesum'),
      ],
    };
    const competingMwe: ReleaseRow = {
      card_id: 'wc_amb000000002',
      card_kind: 'mwe',
      card_version: 'cv_amb2',
      status: 'CANDIDATE',
      known_gaps: [],
      fields: [
        mkField('wc_amb000000002', 'mwe_form', 'вираз А', 'ulif'),
        mkField('wc_amb000000002', 'mwe_form', 'вираз Б', 'frazeolohichnyi'),
      ],
    };
    for (const [row, expected] of [[competingSpelling, 'варіант1 / варіант2'], [competingMwe, 'вираз А / вираз Б']] as const) {
      expect(cardHeading(readableEntry(row, 1))).toEqual({ title: expected, heading: expected, hasText: true });
      const dom = parseDom(renderToStaticMarkup(<WordCardPreview card={{ kind: 'release-card', row, pin }} current={null} compare={false} />));
      expect(dom.querySelector('[data-entry] h2')?.textContent).toBe(expected);
      expect(dom.querySelector('[data-sources-differ]')).not.toBeNull();
    }
  });

  it('flags empty or null core, sense and definition values as missing and never badges null CEFR (F3)', () => {
    const row: ReleaseRow = {
      card_id: 'wc_emp000000001',
      card_kind: 'lexeme',
      card_version: 'cv_emp',
      status: 'CANDIDATE',
      known_gaps: [],
      fields: [
        mkField('wc_emp000000001', 'spelling', 'замок'),
        mkField('wc_emp000000001', 'stress', '   '),
        mkField('wc_emp000000001', 'pos', null),
        mkField('wc_emp000000001', 'cefr', null),
        mkField('wc_emp000000001', 'sense_label', null, 'ulif', { kind: 'sense', id: 'ws_1' }),
        mkField('wc_emp000000001', 'definition_uk', null, 'ulif', { kind: 'sense', id: 'ws_1' }),
      ],
    };
    const dom = parseDom(renderToStaticMarkup(<WordCardPreview card={{ kind: 'release-card', row, pin }} current={null} compare={false} />));
    // Empty stress falls back to spelling instead of blank heading.
    expect(dom.querySelector('[data-entry] h2')?.textContent).toBe('замок');
    expect(dom.querySelector('.wc-cefr-badge')).toBeNull();
    // Unusable null/blank values must not render as readable fact values outside collapsed audit.
    const visibleText = Array.from(dom.querySelectorAll('[data-entry] [data-fact-value]')).map(el => el.textContent);
    expect(visibleText).toEqual(['замок']);
    expect(dom.querySelector('[data-entry]')?.textContent).not.toContain('null');
    for (const field of ['stress', 'pos', 'cefr', 'sense_label', 'definition_uk']) {
      expect(dom.querySelector(`[data-missing-field="${field}"]`), field).not.toBeNull();
    }
    // Every raw assertion remains verbatim in the collapsed audit.
    expect(dom.querySelectorAll('details[data-card-audit] [data-release-assertion]')).toHaveLength(6);
  });

  it('rejects synonym-style objects on non-synonym fields and flags empty-form paradigms as missing (F3)', () => {
    const row: ReleaseRow = {
      card_id: 'wc_obj000000001',
      card_kind: 'lexeme',
      card_version: 'cv_obj',
      status: 'CANDIDATE',
      known_gaps: [],
      fields: [
        mkField('wc_obj000000001', 'spelling', 'замок'),
        mkField('wc_obj000000001', 'stress', { members: 'за́мок' }),
        mkField('wc_obj000000001', 'pos', { members: 'noun' }),
        mkField('wc_obj000000001', 'cefr', { members: 'B1' }, 'puls'),
        mkField('wc_obj000000001', 'sense_label', { members: 'будівля' }, 'ulif', { kind: 'sense', id: 'ws_1' }),
        mkField('wc_obj000000001', 'definition_uk', { members: 'споруда' }, 'ulif', { kind: 'sense', id: 'ws_1' }),
        mkField('wc_obj000000001', 'paradigm', { slot: 'v_naz.s', forms: [] }),
        mkField('wc_obj000000001', 'paradigm', { slot: 'v_rod.s', forms: ['   '] }),
        mkField('wc_obj000000001', 'paradigm', { slot: 'v_dav.s', forms: 'not-a-list' }),
        mkField('wc_obj000000001', 'paradigm', { slot: 'v_dav.s', forms: ['test-form', null] }),
        mkField('wc_obj000000001', 'paradigm', { slot: 'v_oru.s', forms: ['num-form', 123] }),
        mkField('wc_obj000000001', 'paradigm', { slot: 'v_naz.s', forms: ['sense-form'] }, 'ulif', { kind: 'sense', id: 'ws_1' }),
        mkField('wc_obj000000001', 'paradigm', { slot: 'v_naz.s', forms: ['link-form'] }, 'ulif', { kind: 'link', id: 'wl_1' }),
      ],
    };
    const objPage = groupReleasePages([row]).pages[0]!;
    for (const [label, html] of [
      ['release-card', renderToStaticMarkup(<WordCardPreview card={{ kind: 'release-card', row, pin }} current={null} compare={false} />)],
      ['release-page', renderToStaticMarkup(<WordCardPreview card={{ kind: 'release-page', page: objPage, pin }} current={null} compare={false} />)],
    ] as const) {
      const dom = parseDom(html);
      expect(dom.querySelector('[data-entry] h2')?.textContent, label).toBe(label === 'release-page' ? '1. замок' : 'замок');
      expect(dom.querySelector('.wc-cefr-badge'), label).toBeNull();
      // No unusable value or raw JSON leaks into readable facts outside the closed audit.
      const readableClone = dom.querySelector('[data-entry]')?.cloneNode(true) as HTMLElement | null;
      readableClone?.querySelectorAll('details').forEach(el => el.remove());
      const readableText = readableClone?.textContent ?? '';
      for (const leaked of ['за́мок', 'noun', 'B1', 'будівля', 'споруда', 'not-a-list', 'test-form', 'num-form', 'sense-form', 'link-form', '{"slot"']) {
        expect(readableText, `${label}: ${leaked}`).not.toContain(leaked);
      }
      expect(dom.querySelector('[data-fact="paradigm"]'), label).toBeNull();
      for (const field of ['stress', 'pos', 'cefr', 'sense_label', 'definition_uk']) {
        expect(dom.querySelector(`[data-missing-field="${field}"]`), `${label}: ${field}`).not.toBeNull();
      }
      expect(dom.querySelector('[data-missing-paradigm]')?.textContent, label).toContain('No usable paradigm forms');
      expect(dom.querySelector('[data-paradigm-source="ulif"] td')?.textContent, label).toContain('no usable form supplied');
      // Exhaustive assertion coverage and raw audit records remain intact.
      const cited = Array.from(dom.querySelectorAll('[data-assertions]'))
        .filter(el => !el.closest('details'))
        .flatMap(el => (el.getAttribute('data-assertions') ?? '').split(' '))
        .filter(Boolean)
        .sort();
      expect(cited, label).toEqual(row.fields.map(f => f.assertion_id).sort());
      expect(dom.querySelectorAll('details [data-release-assertion]'), label).toHaveLength(13);
    }

    // Mixed usable + unusable assertions on the same field must neither render the unusable value
    // nor trigger a false "Sources differ." conflict marker on either release-card or release-page.
    const mixedPosRow: ReleaseRow = {
      card_id: 'wc_mix000000001',
      card_kind: 'lexeme',
      card_version: 'cv_mix',
      status: 'CANDIDATE',
      known_gaps: [],
      fields: [
        mkField('wc_mix000000001', 'spelling', 'читати'),
        mkField('wc_mix000000001', 'pos', 'verb', 'ulif'),
        mkField('wc_mix000000001', 'pos', { members: 'noun' }, 'vesum'),
      ],
    };
    const mixedPage = groupReleasePages([mixedPosRow]).pages[0]!;
    for (const html of [
      renderToStaticMarkup(<WordCardPreview card={{ kind: 'release-card', row: mixedPosRow, pin }} current={null} compare={false} />),
      renderToStaticMarkup(<WordCardPreview card={{ kind: 'release-page', page: mixedPage, pin }} current={null} compare={false} />),
    ]) {
      const mixedDom = parseDom(html);
      expect(Array.from(mixedDom.querySelectorAll('[data-fact="pos"] [data-fact-value]')).map(el => el.textContent)).toEqual(['verb']);
      expect(mixedDom.querySelector('[data-fact="pos"] [data-sources-differ]')).toBeNull();
      expect(mixedDom.querySelector('[data-fact="pos"]')?.textContent).not.toContain('noun');
      expect(mixedDom.querySelector('[data-missing-field="aspect"]')).not.toBeNull();
      expect(mixedDom.querySelector('[data-missing-field="gender"]')).toBeNull();
      expect(mixedDom.querySelectorAll('details [data-release-assertion]')).toHaveLength(3);
    }

    // F3: blank or whitespace paradigm slots with non-empty forms must not render in any table
    // and must not suppress the missing-paradigm marker, while preserving raw assertions in audit.
    for (const blankSlot of ['', '   ']) {
      const blankSlotRow: ReleaseRow = {
        card_id: 'wc_bslot000001',
        card_kind: 'lexeme',
        card_version: 'cv_bslot',
        status: 'CANDIDATE',
        known_gaps: [],
        fields: [
          mkField('wc_bslot000001', 'spelling', 'ключ'),
          mkField('wc_bslot000001', 'paradigm', { slot: blankSlot, forms: ['ключ'] }),
        ],
      };
      const blankDom = parseDom(renderToStaticMarkup(<WordCardPreview card={{ kind: 'release-card', row: blankSlotRow, pin }} current={null} compare={false} />));
      expect(blankDom.querySelector('[data-paradigm-source]'), JSON.stringify(blankSlot)).toBeNull();
      expect(blankDom.querySelector('table'), JSON.stringify(blankSlot)).toBeNull();
      expect(blankDom.querySelector('[data-missing-paradigm]')?.textContent, JSON.stringify(blankSlot)).toContain('No usable paradigm forms');
      expect(blankDom.querySelectorAll('details[data-card-audit] [data-release-assertion]'), JSON.stringify(blankSlot)).toHaveLength(2);
    }
  });

  it('keeps withdrawal warning visible while placing verbatim withdrawal JSON inside collapsed audit (F4)', () => {
    const row: ReleaseRow = {
      card_id: 'wc_wdr000000001',
      card_kind: 'lexeme',
      card_version: 'cv_wdr',
      status: 'CANDIDATE',
      known_gaps: [],
      fields: [mkField('wc_wdr000000001', 'spelling', 'замок')],
    };
    const withdrawalNotice = {
      schema_version: 'word-card-withdrawal.v1',
      previous_release_version: 'v0',
      previous_dataset_sha256: '1'.repeat(64),
      replacement_release_version: 'v-test',
      replacement_dataset_sha256: 'a'.repeat(64),
      withdrawal: { selector: { source_id: 'ulif' }, justification: 'Test withdrawal' },
      removed_field_citations: 2,
    };
    const singleDom = parseDom(renderToStaticMarkup(
      <WordCardPreview card={{ kind: 'release-card', row, pin, withdrawalNotice }} current={null} compare={false} />,
    ));
    expect(singleDom.querySelector('[data-withdrawal-warning]')?.textContent).toContain('2 field citations removed');
    expect(Array.from(singleDom.querySelectorAll('pre')).filter(pre => !pre.closest('details'))).toEqual([]);
    expect(singleDom.querySelector('details[data-card-audit] [aria-label="Withdrawal notice"] pre')?.textContent)
      .toBe(JSON.stringify(withdrawalNotice, null, 2));

    const page = groupReleasePages([row]).pages[0]!;
    const groupedDom = parseDom(renderToStaticMarkup(
      <WordCardPreview card={{ kind: 'release-page', page, pin, withdrawalNotice }} current={null} compare={false} />,
    ));
    expect(groupedDom.querySelector('[data-withdrawal-warning]')?.textContent).toContain('2 field citations removed');
    expect(Array.from(groupedDom.querySelectorAll('pre')).filter(pre => !pre.closest('details'))).toEqual([]);
    expect(groupedDom.querySelector('details[data-page-audit] [aria-label="Withdrawal notice"] pre')?.textContent)
      .toBe(JSON.stringify(withdrawalNotice, null, 2));
  });

  it('shows all missing fields explicitly on minimal MWE cards like Гнат-безп\'ятко', () => {
    const mwe: ReleaseRow = {
      card_id: 'wc_7a6x6n8rek4y',
      card_kind: 'mwe',
      card_version: 'cv_mwe',
      status: 'CANDIDATE',
      known_gaps: [],
      fields: [mkField('wc_7a6x6n8rek4y', 'mwe_form', "Гнат-безп'ятко", 'frazeolohichnyi')],
    };
    const page = groupReleasePages([mwe]).pages[0]!;
    const dom = parseDom(renderToStaticMarkup(<WordCardPreview card={{ kind: 'release-page', page, pin }} current={null} compare={false} />));

    expect(dom.querySelector('[data-entry="wc_7a6x6n8rek4y"] h2')?.textContent).toBe("1. Гнат-безп'ятко");
    const missing = Array.from(dom.querySelectorAll('[data-missing-field]')).map(el => el.getAttribute('data-missing-field'));
    expect(missing).toEqual(['stress', 'pos', 'cefr', 'sense_label', 'definition_uk']);
    expect(dom.querySelector('[data-missing-paradigm]')).not.toBeNull();
  });

  it('escapes untrusted HTML and blocks non-allowlisted links on release-card', () => {
    const row: ReleaseRow = {
      card_id: 'wc_xss000000001',
      card_kind: 'lexeme',
      card_version: 'cv_xss',
      status: 'CANDIDATE',
      known_gaps: ['<svg onload=alert(1)>'],
      fields: [
        mkField('wc_xss000000001', 'spelling', '<script>alert(1)</script>', 'evil'),
        mkField('wc_xss000000001', 'definition_uk', '<img src=x onerror=alert(1)>', 'evil'),
      ],
    };
    const html = renderToStaticMarkup(<WordCardPreview card={{ kind: 'release-card', row, pin }} current={null} compare={false} />);
    expect(html).not.toContain('<script>');
    expect(html).not.toContain('<img src=x');
    expect(html).not.toContain('<svg onload');
    const dom = parseDom(html);
    const hrefs = Array.from(dom.querySelectorAll('a')).map(a => a.getAttribute('href') ?? '');
    expect(hrefs.filter(h => h.includes('evil.invalid') || h.startsWith('javascript:'))).toEqual([]);
    expect(dom.querySelector('[data-entry] h2')?.textContent).toBe('<script>alert(1)</script>');
    expect(dom.querySelector('[data-fact="definition_uk"] [data-fact-value]')?.textContent).toBe('<img src=x onerror=alert(1)>');
  });
});

// Mechanically verifies all 150 real pinned release cards when configured locally.
describe.runIf(process.env.ATLAS_WORD_CARD_PUBLIC_PROOF_PATH)('actual release v0.1.0-pilot readable cards (150/150)', () => {
  const loaded = process.env.ATLAS_WORD_CARD_PUBLIC_PROOF_PATH
    ? loadWordCardRelease({
        enabled: true,
        public: true,
        artifactPath: process.env.ATLAS_WORD_CARD_PUBLIC_PROOF_PATH,
        pin: JSON.stringify(publicReleasePin),
      })
    : null;

  it('renders all 150 release-card views headword-first with collapsed audit, faithful assertions and explicit gaps', () => {
    expect(loaded?.kind).toBe('release');
    if (loaded?.kind !== 'release') throw Error('Missing actual release');
    expect(loaded.rows).toHaveLength(150);

    let totalAssertions = 0;
    for (const row of loaded.rows) {
      const entry = readableEntry(row, 1);
      const html = renderToStaticMarkup(
        <WordCardPreview card={{ kind: 'release-card', row, pin: loaded.pin }} current={null} compare={false} />,
      );
      const dom = parseDom(html);
      // Headword-first, never internal card_id in h2.
      expect(dom.querySelector('[data-entry] h2')?.textContent, row.card_id).toBe(entry.heading);
      expect(dom.querySelector('[data-entry] h2')?.textContent, row.card_id).not.toContain(row.card_id);
      // No raw JSON <pre> outside collapsed <details>.
      expect(Array.from(dom.querySelectorAll('pre')).filter(pre => !pre.closest('details')), row.card_id).toEqual([]);
      const audit = dom.querySelector(`details[data-card-audit="${row.card_id}"]`);
      expect(audit?.hasAttribute('open'), row.card_id).toBe(false);
      expect(audit?.querySelector(':scope > summary')?.textContent, row.card_id).toBe('Sources and audit');
      // Every assertion of this card is cited in the readable view AND preserved verbatim in audit.
      const readableIds = Array.from(dom.querySelectorAll('[data-assertions]'))
        .filter(el => !el.closest('details'))
        .flatMap(el => (el.getAttribute('data-assertions') ?? '').split(' '))
        .filter(Boolean)
        .sort();
      const auditIds = Array.from(audit?.querySelectorAll('[data-release-assertion]') ?? [])
        .map(el => el.getAttribute('data-release-assertion') ?? '')
        .sort();
      const expectedIds = row.fields.map(f => f.assertion_id).sort();
      expect(readableIds, row.card_id).toEqual(expectedIds);
      expect(auditIds, row.card_id).toEqual(expectedIds);
      // Every missing core field is shown explicitly.
      if (!row.fields.some(f => f.field === 'stress')) expect(dom.querySelector('[data-missing-field="stress"]'), row.card_id).not.toBeNull();
      if (!row.fields.some(f => f.field === 'pos')) expect(dom.querySelector('[data-missing-field="pos"]'), row.card_id).not.toBeNull();
      if (!row.fields.some(f => f.field === 'cefr')) expect(dom.querySelector('[data-missing-field="cefr"]'), row.card_id).not.toBeNull();
      if (!row.fields.some(f => f.field === 'sense_label')) expect(dom.querySelector('[data-missing-field="sense_label"]'), row.card_id).not.toBeNull();
      if (!row.fields.some(f => f.field === 'definition_uk')) expect(dom.querySelector('[data-missing-field="definition_uk"]'), row.card_id).not.toBeNull();
      if (!row.fields.some(f => f.field === 'paradigm')) expect(dom.querySelector('[data-missing-paradigm]'), row.card_id).not.toBeNull();
      totalAssertions += row.fields.length;
    }
    expect(totalAssertions).toBe(2978);
  });
});
