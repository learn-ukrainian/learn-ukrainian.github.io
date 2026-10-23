import { defineConfig, devices } from '@playwright/test';

// Actual Pages-style C37 proof. The suite starts the existing GH-Pages 404 server
// for ATLAS_WORD_CARD_C37_ROOT (and optionally the controls root) and skips when
// neither is configured, so the default Playwright run never needs it.
export default defineConfig({
  testDir: './e2e',
  testMatch: 'word-card-preview.spec.ts',
  grep: /C37/,
  fullyParallel: false,
  timeout: 30_000,
  expect: { timeout: 15_000 },
  reporter: process.env.CI ? [['github'], ['list']] : 'list',
  use: { trace: 'retain-on-failure' },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
});
