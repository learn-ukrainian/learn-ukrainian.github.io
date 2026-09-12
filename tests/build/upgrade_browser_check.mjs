// Build and browse generated lesson MDX with the real Astro/React components.
// Usage from repository root: node tests/build/upgrade_browser_check.mjs PATH_TO_MDX
// Requires site dependencies and Playwright Chromium. No network/model calls.
// Emits JSON evidence; exits nonzero on route, tab, build, or browser errors.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import http from 'node:http';
import { createRequire } from 'node:module';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';

const root = process.cwd();
const site = path.join(root, 'site');
const require = createRequire(path.join(site, 'package.json'));
const { chromium } = require('playwright');
const source = path.resolve(process.argv[2] || 'batch_state/cu-p1-gold/assembled');
// Keep output below site so prerender resolves the same installed dependencies.
const temp = fs.mkdtempSync(path.join(site, '.upgrade-browser-'));
const pages = path.join(temp, 'src/pages/a1/things-have-gender');
const dist = path.join(temp, 'dist');
fs.mkdirSync(pages, { recursive: true });
for (const name of ['index', '1', '2', '3']) {
  fs.copyFileSync(path.join(source, `${name}.mdx`), path.join(pages, `${name}.mdx`));
}
const moduleUrl = (name) => pathToFileURL(require.resolve(name)).href;
const config = path.join(temp, 'astro.config.mjs');
fs.writeFileSync(config, `
import {defineConfig} from ${JSON.stringify(moduleUrl('astro/config'))};
import mdx from ${JSON.stringify(moduleUrl('@astrojs/mdx'))};
import react from ${JSON.stringify(moduleUrl('@astrojs/react'))};
import {unified} from ${JSON.stringify(moduleUrl('@astrojs/markdown-remark'))};
import remarkGfm from ${JSON.stringify(moduleUrl('remark-gfm'))};
export default defineConfig({
  srcDir:${JSON.stringify(path.join(temp, 'src'))}, outDir:${JSON.stringify(dist)},
  integrations:[mdx(),react()], markdown:{processor:unified({remarkPlugins:[remarkGfm]})},
  vite:{resolve:{alias:{'@site':${JSON.stringify(site)},
    '@astrojs/starlight/components':${JSON.stringify(path.join(site, 'src/starlight-compat/index.ts'))}},
    dedupe:['react','react-dom']}}
});
`);
const built = spawnSync(process.execPath, [path.join(site, 'node_modules/.bin/astro'), 'build', '--root', site, '--config', path.relative(site, config)],
  { cwd: root, encoding: 'utf8', timeout: 120000 });
assert.equal(built.status, 0, built.stdout + built.stderr);
console.log('ASTRO_FIXTURE_BUILD: PASS (4 generated pages)');
const server = http.createServer((request, response) => {
  let file = path.join(dist, decodeURIComponent(new URL(request.url, 'http://localhost').pathname));
  if (!file.startsWith(dist + path.sep) || !fs.existsSync(file)) {
    response.writeHead(404); response.end(); return;
  }
  if (fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
  response.setHeader('Content-Type', ({ '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css' })[path.extname(file)] || 'application/octet-stream');
  response.end(fs.readFileSync(file));
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const browser = await chromium.launch();
const page = await browser.newPage();
const errors = [];
const facts = [];
page.on('pageerror', error => errors.push(error.message));
try {
  for (const width of [1200, 400]) {
    await page.setViewportSize({ width, height: 900 });
    for (const suffix of ['', '1/', '2/', '3/']) {
      const response = await page.goto(`http://127.0.0.1:${server.address().port}/a1/things-have-gender/${suffix}`);
      assert.equal(response.status(), 200);
      await page.waitForSelector('[role=tab]');
      const tabs = page.getByRole('tab');
      assert.equal(await tabs.count(), 4);
      for (let i = 0; i < 4; i++) {
        await tabs.nth(i).click();
        assert.equal(await page.getByRole('tabpanel').filter({ visible: true }).count(), 1);
      }
      facts.push({ page: suffix || 'index', width, status: response.status(), tabs: 4 });
    }
  }
  assert.deepEqual(errors, []);
  console.log(JSON.stringify({ facts, errors }));
  console.log('GENERATED_LESSON_BROWSER: PASS');
} finally {
  await browser.close();
  server.close();
  // Only this process's newly-created temporary fixture directory is removed.
  fs.rmSync(temp, { recursive: true, force: true });
}
