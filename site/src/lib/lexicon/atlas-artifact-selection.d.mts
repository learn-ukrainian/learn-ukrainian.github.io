import type { Plugin } from "vite";

export const PINNED_SELECTION_ENV: "ATLAS_SEARCH_RUNTIME_TREE";
export const PINNED_ARTIFACT_DIRNAME: ".atlas-pinned";
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
export function browseShardFileNames(meta: unknown, metaPath: string): string[];
export function assertSelectedArtifactsComplete(siteRoot: string, env?: NodeJS.ProcessEnv): void;
export function installSelectedBrowseShards(distDir: string, siteRoot: string, env?: NodeJS.ProcessEnv): void;
export function atlasArtifactSelectionPlugin(options: { siteRoot: string; env?: NodeJS.ProcessEnv }): Plugin;
