import { compile } from '@mdx-js/mdx';
import remarkGfm from 'remark-gfm';
import { describe, expect, it } from 'vitest';

import {
  createEtymologyResolver,
  normalizeLemma,
  resolveVocabWord,
} from '../../src/data/etymology-lemma-index.mjs';
import vocabEtymologyLinker from '../../plugins/vocab-etymology-link.mjs';

const resolver = createEtymologyResolver({
  lemmaRoutes: new Map([
    ['кава', { href: '/lexicon/кава/#etymology', lemma: 'кава', slug: 'kava', polysemy: false }],
    ['субота', { href: '/lexicon/субота/#etymology', lemma: 'субота', slug: 'subota', polysemy: false }],
    [
      'прокидатися',
      {
        href: '/lexicon/прокидатися/#etymology',
        lemma: 'прокидатися',
        slug: 'prokydatysia',
        polysemy: false,
      },
    ],
  ]),
  vesumLemmas: new Map([
    ['суботу', 'субота'],
    ['прокидаюся', 'прокидатися'],
  ]),
});

async function compileMdx(source: string): Promise<string> {
  const compiled = await compile(source, {
    jsx: true,
    remarkPlugins: [remarkGfm, [vocabEtymologyLinker, { resolver }]],
  });
  return String(compiled);
}

describe('vocab etymology linker', () => {
  it('normalizes lowercase and combining stress marks', () => {
    expect(normalizeLemma('Ка́ва')).toBe('кава');
    expect(normalizeLemma('СУБО́ТА')).toBe('субота');
    expect(normalizeLemma('краї́на й')).toBe('країна й');
  });

  it('resolves direct, declined, and reflexive VESUM forms', () => {
    expect(resolveVocabWord('кава', resolver)?.href).toBe('/lexicon/кава/#etymology');
    expect(resolveVocabWord('суботу', resolver)?.href).toBe('/lexicon/субота/#etymology');
    expect(resolveVocabWord('прокидаюся', resolver)?.href).toBe('/lexicon/прокидатися/#etymology');
  });

  it('links matched words in vocabulary tables and leaves misses plain', async () => {
    const compiled = await compileMdx(`
<TabItem label="Vocabulary">

| Word | IPA | English |
| --- | --- | --- |
| кава |  | coffee |
| невідоме |  | unknown |

</TabItem>
`);

    expect(compiled).toContain('href="/lexicon/%D0%BA%D0%B0%D0%B2%D0%B0/#etymology"');
    expect(compiled).toContain('className="vocab-etymology-link"');
    expect(compiled).toContain('data-etymology-slug="kava"');
    expect(compiled).toContain('{"невідоме"}');
    expect(compiled).not.toContain('/etymology/nevidome/');
    expect(compiled).not.toContain('/etymology/kava/');
  });

  it('does not link multi-word phrases or non-vocabulary tabs', async () => {
    const compiled = await compileMdx(`
<TabItem label="Vocabulary">

| Word | IPA | English |
| --- | --- | --- |
| добра кава |  | good coffee |

</TabItem>
<TabItem label="Activities">

| Word | IPA | English |
| --- | --- | --- |
| кава |  | coffee |

</TabItem>
`);

    expect(compiled).not.toContain('href="/lexicon/%D0%BA%D0%B0%D0%B2%D0%B0/#etymology"');
  });

  it('supports Ukrainian vocabulary tabs and table opt-out comments', async () => {
    const compiled = await compileMdx(`
<TabItem label="Словник">

{/* vocab-etymology: off */}
| Слово | Переклад |
| --- | --- |
| кава | coffee |

| Слово | Переклад |
| --- | --- |
| суботу | Saturday |

</TabItem>
`);

    expect(compiled).not.toContain('href="/lexicon/%D0%BA%D0%B0%D0%B2%D0%B0/#etymology"');
    expect(compiled).toContain('href="/lexicon/%D1%81%D1%83%D0%B1%D0%BE%D1%82%D0%B0/#etymology"');
  });

  it('is idempotent when the plugin runs twice', async () => {
    const compiled = await compile(`
<TabItem label="Vocabulary">

| Word | IPA | English |
| --- | --- | --- |
| кава |  | coffee |

</TabItem>
`, {
      jsx: true,
      remarkPlugins: [
        remarkGfm,
        [vocabEtymologyLinker, { resolver }],
        [vocabEtymologyLinker, { resolver }],
      ],
    });

    expect(String(compiled).match(/href="\/lexicon\/%D0%BA%D0%B0%D0%B2%D0%B0\/#etymology"/g)).toHaveLength(1);
  });
});
