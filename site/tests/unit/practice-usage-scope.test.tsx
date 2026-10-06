import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LexiconPractice, { cardData, isMeaningMcEligible } from '@site/src/components/LexiconPractice';
import PracticeDailyDeck from '@site/src/components/PracticeDailyDeck';
import { CHROME_STRINGS } from '@site/src/lib/i18n/chrome';
import { LEARNER_LEVEL_STORAGE_KEY } from '@site/src/lib/lexicon/levels';
import { practiceDisplayGloss, practiceHeritageBoxes } from '@site/src/lib/lexicon/practice-shard-fetch';
import { clearLoadedSrsState, combinePracticeShards, loadState, selectNextPracticeItem } from '@site/src/lib/lexicon/srs';
import type { DailyPracticeDeckSnapshot, PracticeDeckData, PracticeIndexShard, PracticeLexeme, PracticeLexemeShard } from '@site/src/lib/lexicon/srs';
import type { LexiconEntryForSeverity } from '@site/src/lib/lexicon/heritage-severity';

function lexeme(overrides: Partial<PracticeLexeme> = {}): PracticeLexeme {
  return {
    lemmaId: 'krymchanyn', lemma: 'кримчанин', lemmaPlain: 'кримчанин',
    gloss: 'Crimean (Russian calque; standard Ukrainian: legacy suggestion)',
    glossClean: 'Crimean (Russian calque', meaningMcEligible: false,
    ipa: null, pos: 'noun', cefr: 'B2', heritage: 'calque', severity: 'calque_yellow',
    paradigm: { cases: {} }, ...overrides,
  };
}

const legacy = lexeme();
const ordinary = lexeme({
  lemmaId: 'knyha', lemma: 'книга', lemmaPlain: 'книга',
  gloss: 'book; volume', glossClean: 'book', meaningMcEligible: true, heritage: 'native', severity: null,
});
// The same headword-slot evidence fixture as #9691; a source-supported register
// label is retained, without turning the form into a condemned whole word.
const positive: PracticeLexeme & LexiconEntryForSeverity = {
  ...lexeme({ lemmaId: 'gazda', lemma: 'ґазда', lemmaPlain: 'ґазда', gloss: 'master', glossClean: 'master', meaningMcEligible: true, heritage: 'dialect' }),
  heritage_status: { classification: 'dialect', attestations: [] },
  enrichment: { definition_cards: [{ id: 'sum20', definitions: ['ҐАЗДА́, и́, ч., діал. Господар.'] }] },
};

function deck(entries: PracticeLexeme[]): PracticeDeckData {
  return {
    deckVersion: 'scope-fixture', level: 'B2', lexemes: entries, cloze: [],
    index: entries.map((entry, i) => ({
      lemmaId: entry.lemmaId, lemma: entry.lemma, cefr: entry.cefr,
      modes: entry.meaningMcEligible ? ['flashcards', 'choice', 'matching'] : ['flashcards'],
      hasCloze: false, clozeIds: [], newOrder: i,
    })),
  };
}

beforeEach(() => {
  localStorage.clear();
  clearLoadedSrsState();
  localStorage.setItem(LEARNER_LEVEL_STORAGE_KEY, 'B2');
  document.documentElement.lang = 'en';
  document.documentElement.dataset.chromeLocale = 'en';
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify([])));
});

afterEach(() => {
  vi.restoreAllMocks();
  delete document.documentElement.dataset.chromeLocale;
});

describe('Practice usage scope (#9652)', () => {
  test.each(['en', 'uk'] as const)('qualifies legacy commentary and the raw calque chip in %s', (locale) => {
    const card = cardData(legacy, 'B2', locale);
    expect(card.back).toContain('Crimean');
    expect(card.back).toContain('примітка Атласу: «Russian calque; standard Ukrainian: legacy suggestion»');
    expect(card.back).toContain('обсяг застереження не встановлено');
    expect(card.heritageLabel).toContain(CHROME_STRINGS[locale]['practice.heritageCalque']);
    expect(card.heritageLabel).toContain(locale === 'uk' ? 'обсяг застереження не встановлено' : 'scope of caution not established');
    expect(card.tagColor).toBe('var(--lu-text-muted)');
    expect(practiceHeritageBoxes(legacy).usageLabel.scope).toBe('unresolved');
  });

  test.each(['Russian calque', 'russianism', 'surzhyk', 'standard Ukrainian'])('qualifies a truncated %s clause without expanding to the full gloss', (claim) => {
    const entry = lexeme({ glossClean: `Crimean (${claim}` });
    const concise = practiceDisplayGloss(entry, true);
    expect(concise).toContain(`примітка Атласу: «${claim}»`);
    expect(concise).toContain('обсяг застереження не встановлено');
    expect(concise).not.toContain('legacy suggestion');
    expect(concise.length).toBeLessThan(cardData(entry, 'B2', 'en').back.length);
    expect(isMeaningMcEligible(entry)).toBe(false);
  });

  test('keeps an eligible clean option concise while the flashcard retains the full qualified note', () => {
    const entry = lexeme({ glossClean: 'Crimean', meaningMcEligible: true });
    expect(isMeaningMcEligible(entry)).toBe(true);
    expect(practiceDisplayGloss(entry, true)).toBe('Crimean');
    expect(cardData(entry, 'B2', 'en').back).toContain('примітка Атласу: «Russian calque; standard Ukrainian: legacy suggestion»');
  });

  test('renders the clean meaning beside short distractors through the real choice consumer', async () => {
    const entry = lexeme({ glossClean: 'Crimean', meaningMcEligible: true });
    const garden = lexeme({ lemmaId: 'sad', lemma: 'сад', lemmaPlain: 'сад', gloss: 'garden', glossClean: 'garden', meaningMcEligible: true, heritage: 'native', severity: null });
    const fixture = deck([entry, ordinary, positive, garden]);
    fixture.index = fixture.index.filter((row) => row.lemmaId === entry.lemmaId);
    render(<LexiconPractice initialDeck={fixture} deckLevel="B2" autoStart initialMode="choice" />);
    const choice = await screen.findByTestId('practice-choice');
    const labels = Array.from(choice.querySelectorAll('button span:not(.mc-key)'), (span) => span.textContent);
    expect(new Set(labels)).toEqual(new Set(['Crimean', 'book', 'master', 'garden']));
  });

  test('keeps a clean first-sense fallback and an ordinary truncated parenthesis unchanged', () => {
    expect(practiceDisplayGloss(lexeme({ gloss: 'Crimean; resident (Russian calque)', glossClean: undefined }), true)).toBe('Crimean');
    expect(practiceDisplayGloss(lexeme({ glossClean: 'Crimean (resident' }), true)).toBe('Crimean (resident');
  });

  test('keeps ordinary meanings, raw provenance and A1 scaffolding unchanged', () => {
    expect(cardData(ordinary, 'A1', 'en')).toMatchObject({
      back: ordinary.gloss, heritageLabel: 'native', tagColor: 'var(--lu-teal)',
    });
    expect(practiceDisplayGloss(ordinary, true)).toBe('book');
    expect(practiceDisplayGloss(lexeme({ gloss: 'Crimean resident', glossClean: 'Crimean resident' }), true)).toBe('Crimean resident');
  });

  test.each(['en', 'uk'] as const)('preserves a source-supported positive in %s', (locale) => {
    const card = cardData(positive, 'B2', locale);
    expect(practiceHeritageBoxes(positive).usageLabel).toMatchObject({ scope: 'lemma', code: 'dial', authority: ['СУМ-20'] });
    expect(card.back).toBe('master');
    expect(card.heritageLabel).toBe(`${locale === 'uk' ? 'Діалектне слово' : 'Dialect word'} · СУМ-20`);
    expect(card.tagColor).toBe('var(--lu-teal)');
  });

  test.each(['calque', 'avoid', 'russianism'])('qualifies unscoped %s, despite stored severity', (heritage) => {
    const entry = lexeme({ heritage, severity: 'russianism_red' });
    expect(cardData(entry, 'B2', 'en').heritageLabel).toContain('scope of caution not established');
    expect(cardData(entry, 'B2', 'en').tagColor).toBe('var(--lu-text-muted)');
  });

  test.each(['en', 'uk'] as const)('keeps borrowed provenance neutral with its previous colour in %s', (locale) => {
    const entry = lexeme({ heritage: 'borrowed', severity: 'russianism_red' });
    expect(practiceHeritageBoxes(entry).usageLabel.scope).toBe('unresolved');
    expect(cardData(entry, 'B2', locale)).toMatchObject({
      heritageLabel: CHROME_STRINGS[locale]['practice.heritageBorrowed'], tagColor: 'var(--lu-purple)',
    });
  });

  test.each([
    ['loanword', 'borrowed', 'var(--lu-purple)'],
    ['historism', 'historism', 'var(--lu-text-muted)'],
    ['archaism', 'archaism', 'var(--lu-text-muted)'],
    ['dialect', 'dialect', 'var(--lu-text-muted)'],
    ['native', 'native', 'var(--lu-teal)'],
    ['inherited', 'inherited', 'var(--lu-teal)'],
    ['unknown', 'unknown', 'var(--lu-text-muted)'],
  ])('preserves the raw %s chip and colour, despite stored severity', (heritage, heritageLabel, tagColor) => {
    expect(cardData(lexeme({ heritage, severity: 'russianism_red' }), 'B2', 'en')).toMatchObject({ heritageLabel, tagColor });
  });

  test.each([
    ['sense_restricted', 'en'], ['sense_restricted', 'uk'], ['phrasal', 'en'], ['phrasal', 'uk'],
  ] as const)('retains %s as a contextual caution in %s, with unchecked authority qualified', (kind, locale) => {
    const entry = {
      ...legacy,
      heritage_status: { classification: 'calque', curated_calque: { kind, calque_sense: 'fixture context', source: ['unchecked-reference'] } },
    };
    const card = cardData(entry, 'B2', locale);
    expect(practiceHeritageBoxes(entry).usageLabel.scope).toBe(kind === 'phrasal' ? 'phrase' : 'sense');
    expect(card.heritageLabel).toContain(CHROME_STRINGS[locale][kind === 'phrasal' ? 'practice.heritageCalquePhrase' : 'practice.heritageCalqueSense']);
    expect(card.heritageLabel).toContain('fixture context');
    expect(card.heritageLabel).toContain(CHROME_STRINGS[locale]['practice.heritageNoVerifiedExcerpt']);
    expect(card.back).toContain('обсяг застереження не встановлено');
  });

  test('uses the existing current projection for lemma-bound and contextual proof', () => {
    const bound = lexeme({ lemma: 'міроприємство', heritage: 'calque', gloss: 'avoid: захід' });
    expect(practiceHeritageBoxes(bound).usageLabel).toMatchObject({ scope: 'lemma', code: 'calq' });
    expect(cardData(bound, 'B2', 'en').back).toBe('avoid: захід');
    expect(cardData(bound, 'B2', 'en').heritageLabel).toContain('antonenko-davydovych');
    const contextual = lexeme({ lemma: 'приймати', gloss: 'to take' });
    expect(practiceHeritageBoxes(contextual).usageLabel.scope).toBe('phrase');
    expect(cardData(contextual, 'B2', 'en').heritageLabel).toContain('collocation');
    expect(cardData(contextual, 'B2', 'en').back).toBe('to take');
  });

  test('preserves shard identity, lineage, eligibility, deck membership and saved progress', () => {
    const entries = [legacy, ordinary, positive];
    const fixture = deck(entries);
    const meta = { schemaVersion: 1, deckVersion: fixture.deckVersion, level: fixture.level, source: 'fixture-source' };
    const index: PracticeIndexShard = { ...meta, schema: 'atlas-practice-index', items: fixture.index, counts: { lexemes: 3, cloze: 0, clozeEligibleLexemes: 0, clozeCoverage: 0 } };
    const lexemes: PracticeLexemeShard = { ...meta, schema: 'atlas-practice-lexemes', lexemes: entries };
    const loaded = combinePracticeShards(index, lexemes);
    const before = JSON.stringify({ index, lexemes, loaded });
    loadState(localStorage, new Date('2026-10-06T00:00:00Z'));
    const progress = JSON.stringify(localStorage.getItem('lu-lexicon-srs'));
    for (const entry of loaded.lexemes) {
      cardData(entry, 'B2', 'en');
      practiceDisplayGloss(entry, true);
    }
    expect(loaded.lexemes).toBe(entries);
    expect(loaded.index).toBe(index.items);
    expect(JSON.stringify({ index, lexemes, loaded })).toBe(before);
    expect(loaded.lexemes.map(isMeaningMcEligible)).toEqual([false, true, true]);
    expect(JSON.stringify(localStorage.getItem('lu-lexicon-srs'))).toBe(progress);
    for (const entry of entries) {
      const single = { ...loaded, index: loaded.index.filter((row) => row.lemmaId === entry.lemmaId) };
      expect(selectNextPracticeItem(single, { modeFilter: 'flashcards', now: new Date('2026-10-06T00:00:00Z') })?.lemma.lemmaId).toBe(entry.lemmaId);
    }
  });

  test('renders a qualified flashcard back through the real Practice consumer', async () => {
    const user = userEvent.setup();
    const { container } = render(<LexiconPractice initialDeck={deck([legacy])} deckLevel="B2" />);
    await user.click(container.querySelector<HTMLButtonElement>('button[data-mode="flashcards"]')!);
    await screen.findByTestId('practice-stage-shell');
    const card = container.querySelector<HTMLElement>('[data-activity="flashcard"]')!;
    await user.click(card);
    expect(card.dataset.flipped).toBe('true');
    expect(card.querySelector('.flashcard-back')?.textContent).toContain('Crimean');
    expect(card.querySelector('.flashcard-back')?.textContent).toContain('обсяг застереження не встановлено');
    expect(card.querySelector('.flashcard-heritage-chip')?.textContent).toContain('scope of caution not established');
  });

  test('qualifies daily snapshot glosses in both preview and rows without rewriting the snapshot', () => {
    const snapshot: DailyPracticeDeckSnapshot = {
      version: 2, date: '2026-10-06', level: 'B2', deckVersion: 'scope-fixture', createdAt: 0,
      items: [{ lemmaId: legacy.lemmaId, origin: 'new', lemma: legacy.lemma, gloss: legacy.gloss, cefr: legacy.cefr, pos: legacy.pos }],
    };
    const before = JSON.stringify(snapshot);
    const { container } = render(<PracticeDailyDeck
      snapshot={snapshot} rows={{ pendingDue: [], pendingNew: [{ item: snapshot.items[0]!, state: 'new', lastSeenAt: null }], done: [] }}
      lexemes={new Map([[legacy.lemmaId, legacy]])} atlasLemmaHref={(id) => `/lexicon/${id}/`} chromeLocale="en" learnerLevel="B2"
    />);
    expect(container.querySelector('.row-gloss')?.textContent).toContain('обсяг застереження не встановлено');
    expect(container.textContent?.match(/обсяг застереження не встановлено/g)?.length).toBe(2);
    expect(JSON.stringify(snapshot)).toBe(before);
  });
});
