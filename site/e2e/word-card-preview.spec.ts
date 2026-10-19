import { expect, test } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import snapshot from '../tests/fixtures/word-card-preview/current';

// This spec drives an explicitly flag-enabled local build. No data certification.
const names = ['bronia-armour', 'bronia-reservation', 'idiom-buduvaty-povitriani-zamky', 'kliuch-1', 'vriady-hody-conflict', 'vybihaty-imperf', 'vybihty-perf', 'zamok-castle', 'zamok-legacy-split', 'zamok-lock', 'zamok-settlement',
  'control-complete', 'control-conflict', 'control-unverified', 'control-missing', 'control-suppressed', 'control-redirected', 'control-malformed', 'control-mismatched', 'control-internal', 'control-sum11', 'control-untrusted', 'real-data'];
for (const prefix of ['', 'compare/']) {
  for (const name of names) test(`${prefix}${name}`, async ({ page }, testInfo) => {
    await page.goto(`/lexicon-v2/${prefix}${name}/`);
    await expect(page.locator('[data-preview-banner]')).toContainText('not certified learner cards');
    await expect(page.locator('meta[name="robots"]')).toHaveAttribute('content', 'noindex, nofollow');
    await expect(page.locator('[data-input-hash]')).toHaveText(/^[a-f0-9]{64}$/);
    const candidate = page.getByRole('region', { name:'Candidate presentation', exact:true });
    const refused = ['control-suppressed','control-redirected','control-malformed','control-mismatched','real-data','zamok-legacy-split'].includes(name);
    if (refused) await expect(candidate.locator('[data-raw-value]')).toHaveCount(0);
    else for (const group of ['forms', 'stress', 'senses', 'examples', 'citations']) await expect(candidate.getByRole('region',{name:group,exact:true})).toBeVisible();
    if (name === 'control-complete') await expect(candidate.getByText('EXAMPLE_RAW',{exact:true})).toBeVisible();
    if (name === 'control-conflict') await expect(candidate.getByRole('region',{name:'stress',exact:true}).locator('[data-raw-value]')).toHaveCount(0);
    if (name === 'control-unverified') await expect(candidate.getByRole('region',{name:'stress',exact:true}).locator('[data-field-state]')).toHaveText('unverified');
    if (['control-internal','control-sum11'].includes(name)) await expect(candidate.getByRole('region',{name:'stress',exact:true})).toContainText('Source unavailable');
    if (name === 'control-mismatched') await expect(candidate).toContainText('Mismatched selected assertion binding');
    if (name === 'control-untrusted') {
      expect(await candidate.getByRole('region',{name:'stress',exact:true}).locator('[data-raw-value]').textContent()).toBe('<script>globalThis.previewInjected=1</script> RAW  A');
      expect(await page.evaluate(() => Object.hasOwn(globalThis,'previewInjected'))).toBe(false);
    }
    if (name === 'real-data') await expect(candidate).toContainText('Certified real-card export unavailable');
    if (name === 'zamok-castle' || name === 'zamok-lock') {
      await expect(candidate.locator('[data-preview-card]')).toHaveAttribute('data-preview-card',name === 'zamok-castle' ? 'wc_7k3m9q2xw4pd' : 'wc_c2v8n5rt6yhq');
      if (prefix) await expect(candidate).toContainText('Unresolved pairing');
    }
    if (prefix && !refused) {
      await expect(candidate).toContainText('Better/worse unavailable');
      await expect(candidate.locator('[data-result="better"], [data-result="worse"]')).toHaveCount(0);
    }
    if (prefix && name === 'kliuch-1') {
      await expect(page.getByRole('region',{name:'Current presentation',exact:true}).locator('[data-word-atlas]')).toBeVisible();
      const current = snapshot.records[1];
      if (!current) throw Error('Missing current snapshot');
      for (const [key,value] of Object.entries(current.record.entry)) {
        const cell = candidate.locator(`[data-comparison="entry.${key}"] td`).first();
        expect(await cell.textContent()).toBe(typeof value==='string' ? value : JSON.stringify(value,null,2));
      }
    }
    if (name === 'zamok-castle') {
      const bytes=readFileSync(new URL('../../docs/atlas/word-cards/examples/zamok-castle.json',import.meta.url));
      const source: unknown=JSON.parse(bytes.toString());
      if (!source || typeof source!=='object' || !('assertions' in source) || !Array.isArray(source.assertions)) throw Error('Source missing');
      const assertion=source.assertions.find((a: unknown) => a && typeof a==='object' && 'assertion_id' in a && a.assertion_id==='wa_5888b96f6142b2da61ca2973');
      if (!assertion || typeof assertion!=='object' || !('value' in assertion) || typeof assertion.value!=='string') throw Error('Raw source missing');
      expect(await candidate.getByRole('region',{name:'stress',exact:true}).locator('[data-raw-value]').textContent()).toBe(assertion.value);
      await testInfo.attach('source-sha256',{body:createHash('sha256').update(bytes).digest('hex'),contentType:'text/plain'});
    }
    await testInfo.attach('page',{body:await page.screenshot({fullPage:true}),contentType:'image/png'});
  });
}
