import { expect, test } from '@playwright/test';

const phoneDevices = [
  { name: 'iPhone 14', viewport: { width: 390, height: 844 } },
  { name: 'Pixel 7', viewport: { width: 412, height: 915 } },
];

test.describe('Practice touch targets on mobile and desktop (#8383)', () => {
  for (const device of phoneDevices) {
    test.describe(`phone viewport (${device.name} emulation)`, () => {
      test.use({
        viewport: device.viewport,
        hasTouch: true,
        isMobile: true,
      });

      test(`hydrated landing has nonempty controls, smallTargets === 0, and no horizontal overflow (AC-01, AC-02, AC-03)`, async ({
        page,
      }) => {
        await page.goto('/practice/', { waitUntil: 'domcontentloaded' });

        // Wait for React hydration and control rendering (Finding 1)
        const settingsToggle = page.getByTestId('practice-settings-toggle');
        await expect(settingsToggle).toBeVisible({ timeout: 15_000 });

        const firstLevelBtn = page.locator('.k3-levels button').first();
        await expect(firstLevelBtn).toBeVisible({ timeout: 15_000 });

        // Assert a nonempty control set is actually rendered before measuring
        const controls = page.locator('main button:visible, main a[href]:visible');
        const controlCount = await controls.count();
        expect(controlCount).toBeGreaterThan(0);

        // AC-03 & Stop Policy: no horizontal overflow
        const horizontalOverflow = await page.evaluate(
          () => document.documentElement.scrollWidth > window.innerWidth + 1
        );
        expect(horizontalOverflow).toBe(false);

        // AC-01 & AC-02: all visible buttons and links measure at least 44x44px
        const smallTargets = await page.evaluate(() => {
          const vis = (el: Element) => {
            const r = el.getBoundingClientRect();
            return r.width > 0 && r.height > 0;
          };
          return [...document.querySelectorAll('main button, main a[href]')]
            .filter(vis)
            .filter((e) => {
              const r = e.getBoundingClientRect();
              return r.width < 43.9 || r.height < 43.9;
            })
            .map((e) => ({
              tag: e.tagName,
              className: e.className,
              text: (e.textContent || '').trim().slice(0, 30),
              width: e.getBoundingClientRect().width,
              height: e.getBoundingClientRect().height,
            }));
        });
        expect(smallTargets).toEqual([]);

        // Verify settings toggle button measures >= 44x44px
        const toggleBox = await settingsToggle.boundingBox();
        expect(toggleBox).not.toBeNull();
        expect(toggleBox!.width).toBeGreaterThanOrEqual(44);
        expect(toggleBox!.height).toBeGreaterThanOrEqual(44);

        // Open settings drawer and verify close button meets 44x44px minimum
        await settingsToggle.click();
        const closeBtn = page.getByTestId('settings-drawer-close');
        await expect(closeBtn).toBeVisible({ timeout: 5_000 });
        const closeBox = await closeBtn.boundingBox();
        expect(closeBox).not.toBeNull();
        expect(closeBox!.width).toBeGreaterThanOrEqual(44);
        expect(closeBox!.height).toBeGreaterThanOrEqual(44);
      });
    });
  }

  test.describe('desktop viewport (1440x900)', () => {
    test.use({
      viewport: { width: 1440, height: 900 },
      hasTouch: false,
      isMobile: false,
    });

    test('desktop non-goal: desktop controls retain compact sizing and do not inherit 44px mobile touch expansion', async ({
      page,
    }) => {
      await page.goto('/practice/', { waitUntil: 'domcontentloaded' });

      // Wait for React hydration
      const settingsToggle = page.getByTestId('practice-settings-toggle');
      await expect(settingsToggle).toBeVisible({ timeout: 15_000 });

      // Open settings drawer
      await settingsToggle.click();

      // On desktop, the close button retains its compact design (< 44px width)
      const closeBtn = page.getByTestId('settings-drawer-close');
      await expect(closeBtn).toBeVisible({ timeout: 5_000 });
      const closeBox = await closeBtn.boundingBox();
      expect(closeBox).not.toBeNull();
      // Bounding box on desktop is compact (<44px width) because 44px min-width is scoped to mobile
      expect(closeBox!.width).toBeLessThan(44);
    });
  });
});
