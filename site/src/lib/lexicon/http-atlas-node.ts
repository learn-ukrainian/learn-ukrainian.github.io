/**
 * Node-only helpers for HttpAtlasDataSource.
 *
 * Keep `node:*` imports here so the browser-portable core
 * (`http-atlas-data-source.ts`) can load in client bundles.
 */

import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { gunzipSync } from "node:zlib";
import { AtlasDataSourceError } from "./atlas-data-source.ts";
import {
  HttpAtlasDataSource,
  type AtlasDecompress,
  type AtlasFetch,
  type HttpAtlasDataSourceOptions,
} from "./http-atlas-data-source.ts";

/** Node gzip decode via zlib.gunzipSync. */
export const nodeGunzip: AtlasDecompress = (compressed) => gunzipSync(compressed);

/**
 * Read an on-disk runtime shard tree (export root) as an AtlasFetch.
 * Used by parity tests and local Node tooling — not for browser bundles.
 */
export function createFileAtlasFetch(rootDir: string, basePath = "atlas"): AtlasFetch {
  const root = resolve(rootDir, basePath);
  return async (url: string) => {
    const path = resolve(root, url);
    if (!path.startsWith(root)) {
      throw new AtlasDataSourceError("invalid_slug", `refusing path escape: ${url}`);
    }
    try {
      return new Uint8Array(readFileSync(path));
    } catch (error) {
      throw new AtlasDataSourceError("unavailable", `failed to read ${url}: ${String(error)}`);
    }
  };
}

/** Construct HttpAtlasDataSource with Node gunzip as the default decompress hook. */
export function createNodeHttpAtlasDataSource(
  fetchBytes: AtlasFetch,
  options?: Omit<HttpAtlasDataSourceOptions, "decompress"> & { decompress?: AtlasDecompress },
): HttpAtlasDataSource {
  return new HttpAtlasDataSource(fetchBytes, {
    ...options,
    decompress: options?.decompress ?? nodeGunzip,
  });
}
