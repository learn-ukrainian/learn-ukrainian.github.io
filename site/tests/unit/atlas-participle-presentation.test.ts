// @vitest-environment node

import { describe, expect, test } from 'vitest';
import { articleProps } from '../helpers/word-atlas-record';
import { renderWordAtlasArticle } from '../helpers/render-word-atlas-article';

describe('VESUM participle presentation (#5918)', () => {
  test('renders a passive participle as a participle and links its available verb parent', () => {
    const html = renderWordAtlasArticle(articleProps({
      lemma: 'прийнятий',
      url_slug: 'прийнятий',
      gloss: 'accepted; admitted; adopted',
      entry_type: 'lemma',
      pos: 'adj',
      ipa: null,
      primary_source: 'fixture',
      course_usage: [],
      enrichment: {
        morphology: {
          pos: 'прикметник',
          form_count: 2,
          source: 'VESUM',
          forms: [
            { form: 'прийнятий', label: 'чол., називний' },
            { form: 'прийнята', label: 'жін., називний' },
          ],
          paradigm: {
            kind: 'participle',
            voice: 'passive',
            aspect: 'perfective',
            verb: 'прийняти',
            verb_url_slug: 'прийняти',
          },
        },
      },
    }));

    expect(html).toContain('Пасивний дієприкметник доконаного виду');
    expect(html).toContain('href="/lexicon/прийняти"');
    expect(html).toContain('Форми дієприкметника');
    expect(html).toContain('прийнята');
  });
});
