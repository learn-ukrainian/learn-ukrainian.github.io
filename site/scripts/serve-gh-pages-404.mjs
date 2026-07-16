#!/usr/bin/env node
/**
 * Tiny static server with GitHub Pages 404 semantics.
 *
 * Unknown paths return `404.html` with HTTP status 404 (astro preview does not).
 *
 * Usage:
 *   node ./scripts/serve-gh-pages-404.mjs --root dist --port 4177
 */

import { createReadStream, existsSync, statSync } from "node:fs";
import { createServer } from "node:http";
import { extname, join, normalize, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".webp": "image/webp",
  ".woff2": "font/woff2",
  ".gz": "application/gzip",
  ".map": "application/json",
  ".txt": "text/plain; charset=utf-8",
  ".xml": "application/xml; charset=utf-8",
};

function parseArgs(argv) {
  const out = { root: "dist", port: 4177, host: "127.0.0.1" };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--root") out.root = argv[++i];
    else if (arg === "--port") out.port = Number(argv[++i]);
    else if (arg === "--host") out.host = argv[++i];
  }
  return out;
}

function safeJoin(root, requestPath) {
  const decoded = decodeURIComponent(requestPath.split("?")[0] || "/");
  const cleaned = normalize(decoded).replace(/^(\.\.[/\\])+/, "");
  const full = resolve(root, "." + (cleaned.startsWith("/") ? cleaned : `/${cleaned}`));
  if (!full.startsWith(root)) return null;
  return full;
}

function sendFile(res, status, filePath) {
  const type = MIME[extname(filePath).toLowerCase()] || "application/octet-stream";
  res.writeHead(status, { "content-type": type, "cache-control": "no-store" });
  createReadStream(filePath).pipe(res);
}

export function createGhPages404Server(options) {
  const root = resolve(options.root);
  const notFound = join(root, "404.html");
  if (!existsSync(notFound)) {
    throw new Error(`404.html missing under ${root}`);
  }

  const server = createServer((req, res) => {
    const urlPath = req.url || "/";
    let target = safeJoin(root, urlPath);
    if (!target) {
      res.writeHead(400).end("bad path");
      return;
    }

    if (existsSync(target) && statSync(target).isDirectory()) {
      target = join(target, "index.html");
    }

    if (existsSync(target) && statSync(target).isFile()) {
      sendFile(res, 200, target);
      return;
    }

    // Trailing-slash index fallback for `/lexicon/slug` without slash
    if (!urlPath.endsWith("/") && !extname(urlPath.split("?")[0] || "")) {
      const withIndex = safeJoin(root, `${urlPath.replace(/\?.*$/, "")}/index.html`);
      if (withIndex && existsSync(withIndex)) {
        sendFile(res, 200, withIndex);
        return;
      }
    }

    sendFile(res, 404, notFound);
  });

  return {
    server,
    root,
    listen: () =>
      new Promise((resolveListen) => {
        server.listen(options.port, options.host, () => {
          resolveListen({
            host: options.host,
            port: options.port,
            baseUrl: `http://${options.host}:${options.port}`,
          });
        });
      }),
    close: () =>
      new Promise((resolveClose, reject) => {
        server.close((err) => (err ? reject(err) : resolveClose()));
      }),
  };
}

const isMain =
  process.argv[1] &&
  resolve(fileURLToPath(import.meta.url)) === resolve(process.argv[1]);

if (isMain) {
  const args = parseArgs(process.argv.slice(2));
  const app = createGhPages404Server(args);
  const info = await app.listen();
  console.log(`GH-Pages 404 server at ${info.baseUrl} (root=${app.root})`);
}
