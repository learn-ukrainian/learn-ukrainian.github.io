import { AxeBuilder } from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

// The accepted public denominator. These are real routes, never fixture replacements.
const entries = [
  ['кричачи', 'bare'], ['найактивніше', 'bare'], ['самолікуватися', 'bare'],
  ['абак', 'thin'], ['абака', 'thin'], ['аби-то', 'thin'],
  ['а', 'rich'], ['абажур', 'rich'], ['абат', 'rich'],
  ['виникати', 'heteronym'],
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
          } else if (tier !== 'heteronym') {
            await expect(note).toHaveAttribute('data-atlas-tier', tier);
            await expect(note.locator(`p [data-loc="${locale}"]`)).toBeVisible();
            await expect(note.locator(`p [data-loc="${locale === 'en' ? 'uk' : 'en'}"]`)).toBeHidden();
            await expect(note.locator('[aria-live], [role="status"]')).toHaveCount(0);
            await expect(article.locator('.atlas-overview-card.pending')).toHaveCount(0);
            const details = note.locator('details.marked-forms.atlas-source-waiting');
            await expect(details).toHaveCount(1);
            await expect(details).not.toHaveAttribute('open', '');
            await expect(details.locator('ul')).toBeHidden();
            await expect(details.locator(`summary [data-loc="${locale}"]`)).toHaveText(
              locale === 'en' ? 'Layers awaiting sources' : 'Розділи, що очікують на джерела');
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
            await expect(details.locator('ul')).toBeHidden();
            // Space also toggles the native disclosure without moving focus.
            await page.keyboard.press('Space');
            await expect(details).toHaveAttribute('open', '');
            await expect(details.locator('ul')).toBeVisible();
            await page.keyboard.press('Space');
            await expect(details).not.toHaveAttribute('open', '');
          }
          if (tier === 'heteronym') {
            const tabs = article.getByRole('tab');
            expect(await tabs.count()).toBeGreaterThan(1);
            const assertSelectedTab = async (index: number) => {
              const selected = tabs.nth(index);
              await expect(selected).toHaveAttribute('aria-selected', 'true');
              await expect(selected).toHaveAttribute('tabindex', '0');
              await expect(selected).toBeFocused();
              const panelId = await selected.getAttribute('aria-controls');
              expect(panelId).toBeTruthy();
              await expect(article.locator(`#${panelId}`)).toBeVisible();
              await expect(article.locator('[role="tabpanel"]:visible')).toHaveCount(1);
              await selected.evaluate(async (tab) => {
                await Promise.all(tab.getAnimations().map((animation) => animation.finished));
              });
              // Measure actual rendered text/background, including the smaller hint.
              const contrast = await selected.evaluate((tab) => {
                const channels = (color: string) => color.match(/[\d.]+/g)!.map(Number);
                const luminance = (rgb: number[]) => {
                  const linear = rgb.map((v) => {
                    const s = v / 255;
                    return s <= 0.04045 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
                  });
                  return linear[0] * 0.2126 + linear[1] * 0.7152 + linear[2] * 0.0722;
                };
                const background = getComputedStyle(tab).backgroundColor;
                return Array.from(tab.querySelectorAll('strong, span')).map((node) => {
                  const foreground = getComputedStyle(node).color;
                  const fg = channels(foreground);
                  const bg = channels(background).slice(0, 3);
                  const alpha = fg[3] ?? 1;
                  const rendered = fg.slice(0, 3).map((v, i) => v * alpha + bg[i] * (1 - alpha));
                  const values = [luminance(rendered), luminance(bg)].sort((a, b) => b - a);
                  return { foreground, background, ratio: (values[0] + 0.05) / (values[1] + 0.05) };
                });
              });
              expect(contrast.length).toBeGreaterThan(0);
              await testInfo.attach(`tab-${index}-contrast`, {
                body: JSON.stringify(contrast, null, 2), contentType: 'application/json',
              });
              for (const text of contrast) expect(text.ratio).toBeGreaterThanOrEqual(4.5);
              const tabAxe = await new AxeBuilder({ page }).analyze();
              await testInfo.attach(`tab-${index}-axe`, {
                body: JSON.stringify(tabAxe, null, 2), contentType: 'application/json',
              });
              expect(tabAxe.violations.filter((v) => ['serious', 'critical'].includes(v.impact ?? ''))).toEqual([]);
            };
            await tabs.first().focus();
            await assertSelectedTab(0);
            await page.keyboard.press('ArrowRight');
            await assertSelectedTab(1);
            await page.keyboard.press('Home');
            await assertSelectedTab(0);
            await page.keyboard.press('End');
            await assertSelectedTab(await tabs.count() - 1);
            await page.keyboard.press('ArrowRight');
            await assertSelectedTab(0);
          }
          const atlasButton = article.locator('a.atlas-button');
          await expect(atlasButton).toHaveCSS('text-decoration-line', 'none');
          await expect(atlasButton).toHaveAttribute('href', '/lexicon/');
          await atlasButton.focus();
          await expect(atlasButton).toBeFocused();
          const inTextLinks = article.locator('.atlas-section p a').filter({ visible: true });
          for (const link of await inTextLinks.all()) {
            await expect(link).toHaveCSS('text-decoration-line', 'underline');
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
          await atlasButton.focus();
          await page.keyboard.press('Enter');
          await expect(page).toHaveURL(/\/lexicon\/$/);
        });
      }
    }
  }
}
