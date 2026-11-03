import type { Plugin } from "vite";

export const PINNED_SELECTION_ENV: "ATLAS_SEARCH_RUNTIME_TREE";
export const PINNED_ARTIFACT_DIRNAME: ".atlas-pinned";
export const PINNED_SOURCE_MARKER: "pinned-source.json";
export const PINNED_SHARDS_SIDECAR: "search-shards-source.json";
export const SELECTED_ARTIFACT_NAMES: readonly string[];

export class AtlasArtifactSelectionError extends Error {
  constructor(message: string);
}

export function isPinnedSelection(env?: NodeJS.ProcessEnv): boolean;

export function resolveSelectedArtifactLocations(
  siteRoot: string,
  env?: NodeJS.ProcessEnv,
): {
  mode: "pinned" | "committed";
  committedDataDir: string;
  dataDir: string;
  browseDir: string;
};

export function selectedArtifactPath(name: string, siteRoot: string, env?: NodeJS.ProcessEnv): string;
export function readSelectedArtifactText(name: string, siteRoot: string, env?: NodeJS.ProcessEnv): string;
export function readSelectedArtifactJson(name: string, siteRoot: string, env?: NodeJS.ProcessEnv): unknown;
export function readRuntimeTreeIdentity(treeDir: string): { dataVersion: string; runtimeManifestSha256: string };
export function digestPinnedSet(siteRoot: string, env?: NodeJS.ProcessEnv): { files: Record<string, string>; browse: Record<string, string> };
export function digestDerivedSearchShards(siteRoot: string): Record<string, string>;
export function browseShardFileNames(meta: unknown, metaPath: string): string[];
export function assertSelectedArtifactsComplete(siteRoot: string, env?: NodeJS.ProcessEnv): void;
export function recordDerivedSearchShards(siteRoot: string, env?: NodeJS.ProcessEnv): void;
export function installSelectedBrowseShards(distDir: string, siteRoot: string, env?: NodeJS.ProcessEnv): void;
export function atlasArtifactSelectionPlugin(options: { siteRoot: string; env?: NodeJS.ProcessEnv }): Plugin;
