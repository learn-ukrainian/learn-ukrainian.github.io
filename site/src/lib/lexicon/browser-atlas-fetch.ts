/**
 * Browser `AtlasFetch` for same-origin runtime shards.
 *
 * `HttpAtlasDataSource` already prefixes `assetBaseUrl` (e.g. `/atlas/current.json`);
 * this fetch only performs the network read.
 */

import { AtlasDataSourceError } from "./atlas-data-source.ts";
import type { AtlasFetch } from "./http-atlas-data-source.ts";

export function createBrowserAtlasFetch(
  fetchImpl: typeof fetch = fetch.bind(globalThis),
): AtlasFetch {
  return async (url: string) => {
    let response: Response;
    try {
      response = await fetchImpl(url);
    } catch (error) {
      throw new AtlasDataSourceError(
        "unavailable",
        `network error fetching ${url}: ${String(error)}`,
      );
    }
    if (!response.ok) {
      throw new AtlasDataSourceError(
        "unavailable",
        `HTTP ${response.status} fetching ${url}`,
      );
    }
    const buffer = await response.arrayBuffer();
    return new Uint8Array(buffer);
  };
}

/** Default same-origin atlas asset root (Pages-vendored tree; slice 3). */
export const DEFAULT_ATLAS_ASSET_BASE = "/atlas";
