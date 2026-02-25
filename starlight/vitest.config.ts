/**
 * Vitest configuration — Astro's recommended approach.
 * `getViteConfig` applies the full Astro/Vite pipeline (React JSX transform,
 * CSS modules, tsconfig path aliases) so no extra plugins are needed.
 *
 * https://docs.astro.build/en/guides/testing/#vitest
 */
import { getViteConfig } from 'astro/config';
import { fileURLToPath } from 'node:url';

export default getViteConfig({
  test: {
    environment: 'happy-dom',
    globals: true,
    setupFiles: ['./tests/setup.ts'],
    include: ['tests/unit/**/*.{test,spec}.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov'],
      include: ['src/components/**/*.{ts,tsx}'],
      exclude: ['src/components/Home.tsx', 'src/components/Home.module.css'],
    },
  },
  resolve: {
    alias: {
      // Mirror the tsconfig paths alias so imports work in tests
      '@site': fileURLToPath(new URL('.', import.meta.url)),
    },
  },
});
