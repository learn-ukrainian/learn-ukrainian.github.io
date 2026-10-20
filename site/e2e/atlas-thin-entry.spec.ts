import { AxeBuilder } from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

// The accepted public denominator. These are real routes, never fixture replacements.
const entries = [
  ['кричачи', 'bare'], ['найактивніше', 'bare'], ['самолікуватися', 'bare'],
  ['абак', 'thin'], ['абака', 'thin'], ['аби-то', 'thin'],
  ['а', 'rich'], ['абажур', 'rich'], ['абат', 'rich'],
] as const;

for (const [slug, tier] of entries) {
  for (const width of [1280, 390]) {
    for (const locale of ['en', 'uk'] as const) {
      for (const theme of ['light', 'dark'] as const) {
        test(`${slug} ${tier} ${width}px ${locale} ${theme}`, async ({ page }, testInfo) => {
          await page.setViewportSize({ width, height: width === 390 ? 844 : 800 });
          await page.addInitScript(({ locale, theme }) => {
            localStorage.setItem('lu-chrome-locale', locale);
            localStorage.setItem('lu-theme', theme);
          }, { locale, theme });
          const response = await page.goto(`/lexicon/${encodeURIComponent(slug)}/`);
          expect(response?.status(), `actual reference unavailable: ${slug}`).toBe(200);
          const article = page.locator('[data-word-atlas]');
          await expect(article).toBeVisible();
          await expect(article.locator('h1')).toHaveCount(1);
          await expect(page.locator('html')).toHaveAttribute('data-chrome-locale', locale);
          await page.evaluate((theme) => document.documentElement.setAttribute('data-theme', theme), theme);
          const note = article.locator('.atlas-enrichment-note');
          if (tier === 'rich') {
            await expect(note).toHaveCount(0);
          } else {
            await expect(note).toHaveAttribute('data-atlas-tier', tier);
            await expect(note.locator(`p [data-loc="${locale}"]`)).toBeVisible();
            await expect(note.locator(`p [data-loc="${locale === 'en' ? 'uk' : 'en'}"]`)).toBeHidden();
            await expect(note.locator('[aria-live], [role="status"]')).toHaveCount(0);
            await expect(article.locator('.atlas-overview-card.pending')).toHaveCount(0);
            const details = note.locator('details.marked-forms');
            await details.locator('summary').focus();
            await page.keyboard.press('Enter');
            await expect(details).toHaveAttribute('open', '');
            const gaps = details.locator(`li [data-loc="${locale}"]`);
            expect(await gaps.count()).toBeGreaterThan(0);
            for (const gap of await gaps.allTextContents()) {
              expect(gap).not.toMatch(/^(Course|Style|External materials|Курс|Стилістика|Зовнішні)$/);
            }
            await page.keyboard.press('Enter');
            await expect(details).not.toHaveAttribute('open', '');
          }
          await expect(article.locator('[data-testid="atlas-practice-cta"], [data-testid="atlas-practice-cta-unavailable"]')).toHaveCount(1);
          const emptySections = await article.locator('section.atlas-section').evaluateAll((sections) =>
            sections.filter((section) => {
              if (!section.querySelector('h2')) return false;
              const copy = section.cloneNode(true) as Element;
              copy.querySelector('h2')?.remove();
              return !copy.textContent?.trim();
            }).map((section) => section.querySelector('h2')?.textContent));
          expect(emptySections).toEqual([]);
          const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
          expect(overflow).toBeLessThanOrEqual(1);
          const axe = await new AxeBuilder({ page }).analyze();
          await testInfo.attach('axe', { body: JSON.stringify(axe, null, 2), contentType: 'application/json' });
          await page.screenshot({ path: testInfo.outputPath('entry.png'), fullPage: true });
          await testInfo.attach('entry', { path: testInfo.outputPath('entry.png'), contentType: 'image/png' });
          expect(axe.violations.filter((violation) => ['serious', 'critical'].includes(violation.impact ?? ''))).toEqual([]);
        });
      }
    }
  }
}
