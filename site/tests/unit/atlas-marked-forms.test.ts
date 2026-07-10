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
const MARKED_FORM = 'корисная';
const LEARNER_NOTE = 'не належать до сучасної літературної норми';

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
