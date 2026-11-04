import { defineConfig, devices } from '@playwright/test';
import { HARDENED_CONTEXT_OPTIONS, hardenedLaunchOptions } from './e2e/support/hardened-browser.mjs';

const PORT = process.env.PLAYWRIGHT_PORT ? Number(process.env.PLAYWRIGHT_PORT) : 4321;
const host = '127.0.0.1';
const baseURL = `http://${host}:${PORT}`;

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  timeout: 30_000,
  expect: {
    timeout: 10_000,
  },
  reporter: process.env.CI ? [['github'], ['list']] : 'list',
  use: {
    baseURL,
    trace: 'retain-on-failure',
  },
  webServer: {
    command: `npm run preview -- --host ${host} --port ${PORT}`,
    url: baseURL,
    reuseExistingServer: !process.env.CI,
    timeout: 180_000,
  },
  projects: [
    {
      name: 'chromium',
      // Installed Google Chrome, sandbox on, own origins only (#12689; e2e/support/hardened-browser.mjs).
      use: {
        ...devices['Desktop Chrome'],
        channel: 'chrome',
        launchOptions: hardenedLaunchOptions(),
        ...HARDENED_CONTEXT_OPTIONS,
      },
    },
  ],
});
