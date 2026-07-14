// @vitest-environment node
//
// #4891 — style/register-marked VESUM forms (нестягнені, застарілі, розмовні …) must
// render in a SEPARATE collapsed subsection, never inline with the modern paradigm.
// Renders WordAtlasArticle directly with hand-crafted enrichment (no atlas.db needed).

import reactRenderer from '@astrojs/react/server.js';
import { experimental_AstroContainer as AstroContainer } from 'astro/container';
import { describe, expect, test, beforeAll } from 'vitest';

type AstroComponent = Parameters<AstroContainer['renderToString']>[0];
interface AstroComponentModule {
  default: AstroComponent;
}

const MARKED_SUMMARY = 'Марковані форми (нестягнені, застарілі, розмовні)';
const MARKED_LABEL = 'нестягнена форма';
const ARCHAIC_LABEL = 'застаріла форма';
const SHORT_LABEL = 'коротка форма';
const MARKED_FORM = 'корисная';
const ARCHAIC_FORM = 'дину';
const LEARNER_NOTE = 'не належать до сучасної літературної норми';
const REGISTER_BADGE_SHORT = 'коротка форма';
const REGISTER_BADGE_ARCHAIC = 'застаріле';

/** A корисний-shaped lemma whose нестягнені (:long) forms are segregated by the enricher. */
function makeMorphology(withMarked: boolean) {
  const morphology: Record<string, unknown> = {
    pos: 'прикметник',
    form_count: 4,
    source: 'VESUM',
    forms: [
      { form: 'корисний', label: 'чол., називний' },
      { form: 'корисна', label: 'жін., називний' },
      { form: 'корисне', label: 'сер., називний' },
      { form: 'корисні', label: 'множина, називний' },
    ],
  };
  if (withMarked) {
    morphology.marked_forms = [
      { form: 'корисная', label: 'жін., називний', marker: 'long', marker_label: MARKED_LABEL },
      { form: 'кориснеє', label: 'сер., називний', marker: 'long', marker_label: MARKED_LABEL },
      { form: 'кориснії', label: 'множина, називний', marker: 'long', marker_label: MARKED_LABEL },
    ];
    morphology.marked_form_count = 3;
  }
  return morphology;
}

function makeFullyMarkedMorphology() {
  return {
    pos: 'займенник',
    form_count: 0,
    forms: [],
    source: 'VESUM',
    marked_forms: [
      { form: 'дин', label: 'чол., називний', marker: 'short', marker_label: SHORT_LABEL },
      { form: ARCHAIC_FORM, label: 'чол., родовий', marker: 'short', marker_label: SHORT_LABEL },
    ],
    marked_form_count: 2,
  };
}

function makeFullyMarkedArchaicMorphology() {
  return {
    pos: 'іменник',
    form_count: 0,
    forms: [],
    source: 'VESUM',
    marked_forms: [
      { form: 'горі', label: 'множина, називний', marker: 'arch', marker_label: ARCHAIC_LABEL },
    ],
    marked_form_count: 1,
  };
}

function makeEntry(withMarked: boolean) {
  return {
    lemma: 'корисний',
    url_slug: 'korysnyi',
    gloss: 'useful',
    entry_type: 'lemma',
    pos: 'adj',
    ipa: null,
    primary_source: 'test',
    course_usage: [],
    enrichment: { morphology: makeMorphology(withMarked) },
  };
}

function makeFullyMarkedEntry(kind: 'short' | 'archaic' = 'short') {
  return {
    lemma: kind === 'short' ? 'дин' : 'горі',
    url_slug: kind === 'short' ? 'dyn' : 'hori',
    gloss: null,
    entry_type: 'lemma',
    pos: kind === 'short' ? 'pron' : 'noun',
    ipa: null,
    primary_source: 'test',
    course_usage: [],
    enrichment: {
      morphology: kind === 'short' ? makeFullyMarkedMorphology() : makeFullyMarkedArchaicMorphology(),
    },
  };
}

describe('marked-forms subsection (#4891)', () => {
  let container: AstroContainer;
  let WordAtlasArticle: AstroComponent;

  beforeAll(async () => {
    ({ default: WordAtlasArticle } = (await import(
      '@site/src/lexicon/WordAtlasArticle.astro'
    )) as AstroComponentModule);
    container = await AstroContainer.create();
    container.addServerRenderer({ renderer: reactRenderer });
  });

  function render(withMarked: boolean): Promise<string> {
    return container.renderToString(WordAtlasArticle, {
      props: {
        entry: makeEntry(withMarked),
        allEntries: [],
        generatedAt: 'test',
        manifestVersion: 'test',
      },
    });
  }

  test('marked forms render in a collapsed subsection with a Ukrainian learner note', async () => {
    const html = await render(true);
    // Collapse whitespace: the multi-line JSX learner note renders with newlines the
    // browser folds away, so text assertions compare against a normalised copy.
    const text = html.replace(/\s+/g, ' ');
    // Morphology section and modern paradigm still render.
    expect(html).toContain('Морфологія');
    expect(html).toContain('paradigm-table');
    // Collapsed <details> subsection with the marker-group label + learner note.
    expect(html).toContain('<details');
    expect(html).toContain('class="marked-forms"');
    expect(html).toContain(MARKED_SUMMARY);
    expect(html).toContain(MARKED_LABEL);
    expect(text).toContain(LEARNER_NOTE);
    // The нестягнена form itself is present — inside the marked subsection.
    expect(html).toContain(MARKED_FORM);
    expect(html.indexOf(MARKED_SUMMARY)).toBeLessThan(html.indexOf(MARKED_FORM));
    // No English on this B-level+ surface.
    expect(html).not.toMatch(/marked forms|archaic|colloquial/i);
  });

  test('marked forms never leak into the modern paradigm rows', async () => {
    const html = await render(true);
    // Everything before the marked subsection is the modern paradigm; корисная must
    // appear ONLY after the subsection heading.
    const modernParadigm = html.slice(0, html.indexOf(MARKED_SUMMARY));
    expect(modernParadigm).not.toContain(MARKED_FORM);
    expect(modernParadigm).not.toContain('кориснеє');
    expect(modernParadigm).not.toContain('кориснії');
  });

  test('subsection is absent (no empty shell) when there are no marked forms', async () => {
    const html = await render(false);
    // Modern paradigm still renders …
    expect(html).toContain('Морфологія');
    expect(html).toContain('paradigm-table');
    // … but no marked-forms subsection and none of the marked forms. (Match the class
    // attribute, not the bare slug — the worktree path itself contains "marked-forms".)
    expect(html).not.toContain(MARKED_SUMMARY);
    expect(html).not.toContain('class="marked-forms"');
    expect(html).not.toContain('<details');
    expect(html).not.toContain(MARKED_FORM);
  });
});

describe('fully-marked lemma register treatment (#4900)', () => {
  let container: AstroContainer;
  let WordAtlasArticle: AstroComponent;
  let unmarkedBaseline: string;

  beforeAll(async () => {
    ({ default: WordAtlasArticle } = (await import(
      '@site/src/lexicon/WordAtlasArticle.astro'
    )) as AstroComponentModule);
    container = await AstroContainer.create();
    container.addServerRenderer({ renderer: reactRenderer });
    unmarkedBaseline = await container.renderToString(WordAtlasArticle, {
      props: {
        entry: makeEntry(false),
        allEntries: [],
        generatedAt: 'test',
        manifestVersion: 'test',
      },
    });
  });

  function renderFullyMarked(kind: 'short' | 'archaic' = 'short'): Promise<string> {
    return container.renderToString(WordAtlasArticle, {
      props: {
        entry: makeFullyMarkedEntry(kind),
        allEntries: [],
        generatedAt: 'test',
        manifestVersion: 'test',
      },
    });
  }

  test('unmarked lemma rendering is unchanged', async () => {
    const html = await container.renderToString(WordAtlasArticle, {
      props: {
        entry: makeEntry(false),
        allEntries: [],
        generatedAt: 'test',
        manifestVersion: 'test',
      },
    });
    expect(html).toBe(unmarkedBaseline);
    expect(html).not.toContain('status-badge register');
  });

  test('fully-marked lemma renders a header register badge from the dominant marker', async () => {
    const html = await renderFullyMarked('short');
    expect(html).toContain(`status-badge register`);
    expect(html).toContain(REGISTER_BADGE_SHORT);
    expect(html).not.toContain(REGISTER_BADGE_ARCHAIC);
  });

  test('archaic fully-marked lemma renders the застаріле register badge', async () => {
    const html = await renderFullyMarked('archaic');
    expect(html).toContain(`status-badge register`);
    expect(html).toContain(REGISTER_BADGE_ARCHAIC);
  });

  test('fully-marked lemma suppresses the empty modern paradigm table', async () => {
    const html = await renderFullyMarked('short');
    expect(html).not.toMatch(/0 форм/);
    expect(html).toContain('2 марковані форми');
    // No orphan «Форма | Позначка» shell before the marked block.
    const morphology = html.slice(html.indexOf('Морфологія'), html.indexOf('marked-forms-primary'));
    expect(morphology).not.toContain('<table class="paradigm-table">');
  });

  test('fully-marked lemma renders marked forms expanded, not inside collapsed details', async () => {
    const html = await renderFullyMarked('short');
    expect(html).toContain('class="marked-forms marked-forms-primary"');
    expect(html).not.toContain(MARKED_SUMMARY);
    expect(html).not.toContain('<details');
    const text = html.replace(/\s+/g, ' ');
    expect(text).toContain(LEARNER_NOTE);
    expect(html.indexOf(LEARNER_NOTE)).toBeLessThan(html.indexOf(ARCHAIC_FORM));
  });

  test('partial-marked lemma keeps collapsed details behavior', async () => {
    const html = await container.renderToString(WordAtlasArticle, {
      props: {
        entry: makeEntry(true),
        allEntries: [],
        generatedAt: 'test',
        manifestVersion: 'test',
      },
    });
    expect(html).toContain('class="marked-forms"');
    expect(html).not.toContain('marked-forms-primary');
    expect(html).toContain('<details');
    expect(html).toContain(MARKED_SUMMARY);
    expect(html).not.toContain('status-badge register');
  });
});
