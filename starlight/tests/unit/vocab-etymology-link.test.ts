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
    ['кава', { href: '/etymology/kava/', lemma: 'кава', slug: 'kava', polysemy: false }],
    ['субота', { href: '/etymology/subota/', lemma: 'субота', slug: 'subota', polysemy: false }],
    [
      'прокидатися',
      {
        href: '/etymology/prokydatysia/',
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
    expect(resolveVocabWord('кава', resolver)?.href).toBe('/etymology/kava/');
    expect(resolveVocabWord('суботу', resolver)?.href).toBe('/etymology/subota/');
    expect(resolveVocabWord('прокидаюся', resolver)?.href).toBe('/etymology/prokydatysia/');
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

    expect(compiled).toContain('href="/etymology/kava/"');
    expect(compiled).toContain('className="vocab-etymology-link"');
    expect(compiled).toContain('data-etymology-slug="kava"');
    expect(compiled).toContain('{"невідоме"}');
    expect(compiled).not.toContain('/etymology/nevidome/');
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

    expect(compiled).not.toContain('href="/etymology/kava/"');
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

    expect(compiled).not.toContain('href="/etymology/kava/"');
    expect(compiled).toContain('href="/etymology/subota/"');
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

    expect(String(compiled).match(/href="\/etymology\/kava\/"/g)).toHaveLength(1);
  });
});
