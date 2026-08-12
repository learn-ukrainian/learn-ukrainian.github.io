import { createRequire } from 'node:module';
import { performance } from 'node:perf_hooks';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { mergeConfig, preview } from 'vite';
import { BuildTimeAstroVersionProvider } from '../node_modules/astro/dist/cli/infra/build-time-astro-version-provider.js';
import { piccoloreTextStyler } from '../node_modules/astro/dist/cli/infra/piccolore-text-styler.js';
import { resolveConfig } from '../node_modules/astro/dist/core/config/config.js';
import * as msg from '../node_modules/astro/dist/core/messages/runtime.js';
import { getResolvedHostForHttpServer } from '../node_modules/astro/dist/core/preview/util.js';
import { vitePluginAstroPreview } from '../node_modules/astro/dist/core/preview/vite-plugin-astro-preview.js';
import { rawAtlasShardTransport } from './raw-atlas-shard-transport.mjs';

const require = createRequire(import.meta.url);
const supportedAstroVersion = '7.2.1';
const { version: installedAstroVersion } = require('../node_modules/astro/package.json');

if (installedAstroVersion !== supportedAstroVersion) {
  throw new Error(
    `[raw-atlas-preview] Unsupported Astro ${installedAstroVersion}; this adapter is validated only for Astro ${supportedAstroVersion}.`,
  );
}

/**
 * Astro's static preview server intentionally omits user Vite plugins. This
 * adapter copies its setup, inserts only the raw Atlas transport after Astro's
 * guard plugin, and leaves all non-shard routing to Astro's own static plugin.
 */
export default async function startPreview({
  host,
  outDir,
  port,
  base,
  headers,
  allowedHosts,
  open,
  root,
  logger,
}) {
  const startServerTime = performance.now();
  const outputDir = fileURLToPath(outDir);
  const rootDir = fileURLToPath(root);
  const { astroConfig } = await resolveConfig({ root: rootDir }, 'preview');
  const settings = {
    config: {
      ...astroConfig,
      base,
      outDir,
      root,
      server: {
        ...astroConfig.server,
        allowedHosts,
        headers,
        host,
        open,
        port,
      },
    },
  };
  const astroPreviewConfig = {
    appType: 'mpa',
    base,
    build: { outDir: outputDir },
    configFile: false,
    plugins: [
      vitePluginAstroPreview(settings),
      rawAtlasShardTransport(resolve(outputDir, 'atlas'), base),
    ],
    preview: { headers, host, open, port },
    root: rootDir,
  };
  const userViteConfig = { ...(astroConfig.vite ?? {}) };
  delete userViteConfig.plugins;
  const mergedViteConfig = mergeConfig(userViteConfig, astroPreviewConfig);
  if (typeof allowedHosts === 'boolean' || (Array.isArray(allowedHosts) && allowedHosts.length > 0)) {
    mergedViteConfig.preview ??= {};
    mergedViteConfig.preview.allowedHosts = allowedHosts;
  }

  let previewServer;
  try {
    previewServer = await preview(mergedViteConfig);
  } catch (error) {
    if (error instanceof Error) logger.error(error.stack || error.message);
    throw error;
  }
  previewServer.bindCLIShortcuts({
    customShortcuts: [
      { key: 'r', description: '' },
      { key: 'u', description: '' },
      { key: 'c', description: '' },
      { key: 's', description: '' },
    ],
  });
  logger.info(
    msg.serverStart({
      startupTime: performance.now() - startServerTime,
      resolvedUrls: previewServer.resolvedUrls ?? { local: [], network: [] },
      host,
      base,
      astroVersionProvider: new BuildTimeAstroVersionProvider(),
      textStyler: piccoloreTextStyler,
    }),
  );
  const address = previewServer.httpServer.address();
  const actualPort = address && typeof address === 'object' ? address.port : port;

  return {
    closed: () =>
      new Promise((resolve, reject) => {
        previewServer.httpServer.addListener('close', resolve);
        previewServer.httpServer.addListener('error', reject);
      }),
    host: getResolvedHostForHttpServer(host),
    port: actualPort,
    server: previewServer.httpServer,
    stop: () => previewServer.close(),
  };
}
