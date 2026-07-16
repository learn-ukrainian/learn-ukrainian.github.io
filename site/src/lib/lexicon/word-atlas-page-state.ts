/**
 * Discriminated page states for the Word Atlas article route.
 *
 * SSG (`getStaticPaths`) only emits `ready`. The other variants are dormant
 * shells for a later client/edge reader — defined now so the route can swap
 * sources without a second markup rewrite.
 */

import type { EntryRecord } from "./atlas-data-source.ts";

export type WordAtlasPageState =
  | {
      status: "ready";
      record: EntryRecord;
      generatedAt: string;
      manifestVersion: string;
    }
  | { status: "loading" }
  | { status: "missing"; slug: string }
  | { status: "offline"; message: string; retryable: boolean }
  | {
      status: "version-mismatch";
      expectedVersion: string;
      actualVersion?: string;
    };
