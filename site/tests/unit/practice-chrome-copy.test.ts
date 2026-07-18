// @vitest-environment happy-dom

import { describe, expect, test } from 'vitest';
import { CHROME_STRINGS, type ChromeKey } from '@site/src/lib/i18n/chrome';

describe('practice chrome copy inventory (K3 chunk 1)', () => {
  const practiceKeys = (Object.keys(CHROME_STRINGS.en) as ChromeKey[]).filter((key) =>
    key.startsWith('practice.'),
  );

  test('every practice.* key has a non-empty English and Ukrainian value', () => {
    for (const key of practiceKeys) {
      const en = CHROME_STRINGS.en[key].trim();
      const uk = CHROME_STRINGS.uk[key].trim();
      expect(en.length, `missing English value for ${key}`).toBeGreaterThan(0);
      expect(uk.length, `missing Ukrainian value for ${key}`).toBeGreaterThan(0);
    }
  });

  test('the practice.* key set is identical in both locales', () => {
    const enSet = new Set(practiceKeys);
    const ukSet = new Set(
      (Object.keys(CHROME_STRINGS.uk) as ChromeKey[]).filter((key) => key.startsWith('practice.')),
    );
    expect(ukSet).toEqual(enSet);
  });
});
