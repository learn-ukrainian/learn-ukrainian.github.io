// @vitest-environment node

import { mkdtemp, mkdir, rm, writeFile } from 'node:fs/promises';
import { get as getHttp } from 'node:http';
import { createServer as createTcpServer } from 'node:net';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { createServer, type ViteDevServer } from 'vite';
import { afterEach, describe, expect, test } from 'vitest';
import startPreview from '@site/plugins/astro-raw-atlas-preview.mjs';
import { rawAtlasShardTransport } from '@site/plugins/raw-atlas-shard-transport.mjs';

const rawShard = new Uint8Array([0x1f, 0x8b, 0x08, 0x00, 0x2a, 0x54, 0x5a, 0x01]);
const untouchedAsset = new Uint8Array([0x7b, 0x22, 0x6f, 0x6b, 0x22, 0x3a, 0x74, 0x72, 0x75, 0x65, 0x7d]);
const notFoundPage = '<h1>real Astro 404</h1>';
const temporaryRoots: string[] = [];

type RunningServer = {
  baseUrl: string;
  stop: () => Promise<void>;
};

type HttpResponse = {
  body: Uint8Array;
  headers: Record<string, string | string[] | undefined>;
  status: number;
};

type ReservedPort = {
  close: () => Promise<void>;
  port: number;
};

type PreviewLogger = {
  error: (...args: unknown[]) => void;
  info: (...args: unknown[]) => void;
};

function serverUrl(httpServer: ViteDevServer['httpServer']): string {
  const address = httpServer?.address();
  if (!address || typeof address === 'string') throw new Error('Vite did not expose a TCP address');
  return `http://127.0.0.1:${address.port}`;
}

function get(url: string): Promise<HttpResponse> {
  return new Promise((resolve, reject) => {
    const request = getHttp(url, (response) => {
      const chunks: Uint8Array[] = [];
      response.on('data', (chunk) => chunks.push(chunk));
      response.on('end', () => {
        resolve({
          body: new Uint8Array(Buffer.concat(chunks)),
          headers: response.headers,
          status: response.statusCode ?? 0,
        });
      });
    });
    request.on('error', reject);
  });
}

async function reserveTcpPort(): Promise<ReservedPort> {
  const server = createTcpServer();
  await new Promise<void>((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });
  const address = server.address();
  if (!address || typeof address === 'string') throw new Error('Could not reserve a TCP port');

  return {
    close: () =>
      new Promise((resolve, reject) =>
        server.close((error) => (error ? reject(error) : resolve())),
      ),
    port: address.port,
  };
}

async function writeFixture(assetRoot: string, root: string): Promise<void> {
  await mkdir(join(assetRoot, 'atlas'), { recursive: true });
  await mkdir(join(assetRoot, 'lexicon'), { recursive: true });
  await writeFile(join(assetRoot, 'atlas', 'fixture.json.gz'), rawShard);
  await writeFile(join(assetRoot, 'atlas', 'untouched.json'), untouchedAsset);
  await writeFile(join(assetRoot, 'lexicon', 'index.html'), '<h1>lexicon fixture</h1>');
  await writeFile(join(assetRoot, '404.html'), notFoundPage);
  await writeFile(
    join(root, 'astro.config.mjs'),
    "export default { base: '/preview-base/', trailingSlash: 'always', vite: { preview: { headers: { 'X-Project-Vite': 'merged' }, strictPort: true } } };\n",
  );
}

async function startDev(root: string, publicDir: string): Promise<RunningServer> {
  const server = await createServer({
    appType: 'mpa',
    configFile: false,
    plugins: [rawAtlasShardTransport(join(publicDir, 'atlas'))],
    publicDir,
    root,
    server: { host: '127.0.0.1', port: 0 },
  });
  await server.listen();
  return { baseUrl: serverUrl(server.httpServer), stop: () => server.close() };
}

async function startGuardedPreview(
  root: string,
  outDir: string,
  logger: PreviewLogger = { error: () => {}, info: () => {} },
): Promise<RunningServer> {
  const server = await startPreview({
    allowedHosts: [],
    base: '/preview-base/',
    headers: {},
    host: '127.0.0.1',
    logger,
    open: false,
    outDir: pathToFileURL(outDir),
    port: 0,
    root: pathToFileURL(`${root}/`),
  });
  return { baseUrl: `http://127.0.0.1:${server.port}`, stop: () => server.stop() };
}

async function expectRawShardTransport(server: RunningServer, prefix = ''): Promise<void> {
  const response = await get(`${server.baseUrl}${prefix}/atlas/fixture.json.gz`);
  expect(response.status).toBe(200);
  expect(response.headers['content-encoding'] ?? null).toBeNull();
  expect(response.headers['content-type']?.toString().split(';', 1)[0]).toBe('application/gzip');
  expect(Number(response.headers['content-length'])).toBe(rawShard.byteLength);
  expect(response.body).toEqual(rawShard);
}

async function expectUnchangedAsset(server: RunningServer, prefix = ''): Promise<void> {
  const response = await get(`${server.baseUrl}${prefix}/atlas/untouched.json`);
  expect(response.status).toBe(200);
  expect(response.headers['content-type']?.toString().split(';', 1)[0]).toBe('application/json');
  expect(response.body).toEqual(untouchedAsset);
}

afterEach(async () => {
  await Promise.all(temporaryRoots.splice(0).map((root) => rm(root, { force: true, recursive: true })));
});

describe('raw Atlas shard transport', () => {
  test('logs EADDRINUSE through the single-argument integration logger API', async () => {
    const root = await mkdtemp(join(tmpdir(), 'raw-atlas-shard-transport-'));
    temporaryRoots.push(root);
    const outDir = join(root, 'dist');
    await writeFixture(outDir, root);
    const reservedPort = await reserveTcpPort();
    const errorCalls: unknown[][] = [];

    try {
      await expect(
        startPreview({
          allowedHosts: [],
          base: '/preview-base/',
          headers: {},
          host: '127.0.0.1',
          logger: { error: (...args: unknown[]) => errorCalls.push(args), info: () => {} },
          open: false,
          outDir: pathToFileURL(outDir),
          port: reservedPort.port,
          root: pathToFileURL(`${root}/`),
        }),
      ).rejects.toThrow(`Port ${reservedPort.port} is already in use`);

      expect(errorCalls).toHaveLength(1);
      expect(errorCalls[0]).toHaveLength(1);
      expect(errorCalls[0][0]).toEqual(
        expect.stringContaining(`Port ${reservedPort.port} is already in use`),
      );
    } finally {
      await reservedPort.close();
    }
  });

  test('serves raw shard bytes in real Vite dev and guarded Astro preview servers', async () => {
    const root = await mkdtemp(join(tmpdir(), 'raw-atlas-shard-transport-'));
    temporaryRoots.push(root);
    const publicDir = join(root, 'public');
    const outDir = join(root, 'dist');
    await writeFixture(publicDir, root);
    await writeFixture(outDir, root);

    const dev = await startDev(root, publicDir);
    try {
      await expectRawShardTransport(dev);
      await expectUnchangedAsset(dev);
    } finally {
      await dev.stop();
    }

    const infoCalls: unknown[][] = [];
    const previewServer = await startGuardedPreview(root, outDir, {
      error: () => {},
      info: (...args: unknown[]) => infoCalls.push(args),
    });
    try {
      expect(infoCalls).toHaveLength(1);
      expect(infoCalls[0]).toHaveLength(1);
      expect(infoCalls[0][0]).toEqual(expect.stringContaining('Local'));
      await expectRawShardTransport(previewServer, '/preview-base');
      await expectUnchangedAsset(previewServer, '/preview-base');
      expect(
        (await get(`${previewServer.baseUrl}/preview-base/atlas/untouched.json`)).headers[
          'x-project-vite'
        ],
      ).toBe('merged');

      const slashless = await get(`${previewServer.baseUrl}/preview-base/lexicon`);
      expect(slashless.status).toBe(404);
      expect((await get(`${previewServer.baseUrl}/preview-base/lexicon/`)).status).toBe(200);
      expect((await get(`${previewServer.baseUrl}/atlas/fixture.json.gz`)).status).toBe(404);

      const notFound = await get(`${previewServer.baseUrl}/preview-base/not-here/`);
      expect(notFound.status).toBe(404);
      expect(new TextDecoder().decode(notFound.body)).toBe(notFoundPage);
    } finally {
      await previewServer.stop();
    }
  });
});
