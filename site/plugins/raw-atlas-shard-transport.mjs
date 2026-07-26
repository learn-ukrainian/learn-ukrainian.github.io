import { readFile } from 'node:fs/promises';
import { isAbsolute, relative, resolve, sep } from 'node:path';
import { fileURLToPath, URL } from 'node:url';

const atlasPublicRoot = fileURLToPath(new URL('../public/atlas/', import.meta.url));

/** @param {string} pathname */
const isAtlasShardPath = (pathname) =>
  pathname.startsWith('/atlas/') && pathname.endsWith('.json.gz');

/**
 * @param {string} pathname
 * @param {string} base
 */
const stripBase = (pathname, base) => {
  if (base === '/') return pathname;
  const baseWithoutTrailingSlash = base.endsWith('/') ? base.slice(0, -1) : base;
  if (pathname === base || pathname === baseWithoutTrailingSlash) return '/';
  return pathname.startsWith(`${baseWithoutTrailingSlash}/`)
    ? pathname.slice(baseWithoutTrailingSlash.length)
    : null;
};

/**
 * @param {import('node:http').IncomingMessage} request
 * @param {import('node:http').ServerResponse} response
 * @param {(error?: Error) => void} next
 */
const serveRawAtlasShard = async (atlasRoot, base, request, response, next) => {
  const method = request.method ?? 'GET';
  const pathname = request.url ? new URL(request.url, 'http://localhost').pathname : '';
  const atlasPathname = stripBase(pathname, base);

  if (!['GET', 'HEAD'].includes(method) || !atlasPathname || !isAtlasShardPath(atlasPathname)) {
    next();
    return;
  }

  const filePath = resolve(atlasRoot, `.${atlasPathname.slice('/atlas'.length)}`);
  const relativePath = relative(atlasRoot, filePath);
  if (isAbsolute(relativePath) || relativePath === '..' || relativePath.startsWith(`..${sep}`)) {
    next();
    return;
  }

  try {
    const bytes = await readFile(filePath);
    response.setHeader('Content-Type', 'application/gzip');
    response.setHeader('Content-Length', bytes.length);
    response.removeHeader('Content-Encoding');
    response.end(method === 'HEAD' ? undefined : bytes);
  } catch (error) {
    if (error && typeof error === 'object' && 'code' in error && error.code === 'ENOENT') {
      next();
      return;
    }
    next(error);
  }
};

// Vite invokes these hooks before its static middleware, so no Content-Encoding
// header can be inferred from the .gz filename.
/** @returns {import('vite').Plugin} */
export const rawAtlasShardTransport = (atlasRoot = atlasPublicRoot, base = '/') => ({
  name: 'raw-atlas-shard-transport',
  /** @param {import('vite').ViteDevServer} server */
  configureServer(server) {
    server.middlewares.use((request, response, next) =>
      serveRawAtlasShard(atlasRoot, base, request, response, next),
    );
  },
  /** @param {import('vite').PreviewServer} server */
  configurePreviewServer(server) {
    server.middlewares.use((request, response, next) =>
      serveRawAtlasShard(atlasRoot, base, request, response, next),
    );
  },
});
