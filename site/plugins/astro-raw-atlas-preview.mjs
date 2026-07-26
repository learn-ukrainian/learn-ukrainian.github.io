import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { fileURLToPath, URL } from 'node:url';
import { preview } from 'vite';
import { rawAtlasShardTransport } from './raw-atlas-shard-transport.mjs';

const serveStaticDirectories = () => ({
  name: 'astro-static-directory-preview',
  configurePreviewServer(server) {
    server.middlewares.use((request, _response, next) => {
      const url = new URL(request.url ?? '/', 'http://localhost');
      if (url.pathname.endsWith('/')) request.url = `${url.pathname}index.html${url.search}`;
      next();
    });
  },
});

const serveAstro404 = (outputDir) => ({
  name: 'astro-static-404-preview',
  configurePreviewServer(server) {
    return () => {
      server.middlewares.use(async (request, response, next) => {
        if (!['GET', 'HEAD'].includes(request.method ?? 'GET')) {
          next();
          return;
        }

        try {
          const page = await readFile(resolve(outputDir, '404.html'));
          response.statusCode = 404;
          response.setHeader('Content-Type', 'text/html');
          response.end(request.method === 'HEAD' ? undefined : page);
        } catch (error) {
          next(error);
        }
      });
    };
  },
});

/**
 * Astro's static preview server omits `vite.plugins` by design. Its supported
 * adapter preview entrypoint lets the Atlas transport middleware run before
 * Vite's static-file middleware, just as it does in development.
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
}) {
  const outputDir = fileURLToPath(outDir);
  const previewServer = await preview({
    appType: 'mpa',
    base,
    build: { outDir: outputDir },
    configFile: false,
    plugins: [
      rawAtlasShardTransport(resolve(outputDir, 'atlas')),
      serveStaticDirectories(),
      serveAstro404(outputDir),
    ],
    preview: { allowedHosts, headers, host, open, port },
    root: fileURLToPath(root),
  });
  const address = previewServer.httpServer.address();
  const actualPort = address && typeof address === 'object' ? address.port : port;

  return {
    closed: () =>
      new Promise((resolve, reject) => {
        previewServer.httpServer.addListener('close', resolve);
        previewServer.httpServer.addListener('error', reject);
      }),
    host: typeof host === 'string' ? host : 'localhost',
    port: actualPort,
    server: previewServer.httpServer,
    stop: () => previewServer.close(),
  };
}
