import { existsSync } from "node:fs";
import { readFile, rename, unlink, writeFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { dirname, resolve } from "node:path";
import { gunzipSync } from "node:zlib";

const RECOVERY_COMMAND =
  "gh release download atlas-manifest -p lexicon-manifest.json.gz -O - | gunzip -c > site/src/data/lexicon-manifest.json";

const scriptDir = dirname(decodeURIComponent(new URL(import.meta.url).pathname));
const repoRoot = resolve(scriptDir, "../..");
const pointerPath = resolve(repoRoot, "site/src/data/lexicon-manifest.pointer.json");
const manifestPath = resolve(repoRoot, "site/src/data/lexicon-manifest.json");
const tempPath = `${manifestPath}.tmp`;

function sha256(data) {
  return createHash("sha256").update(data).digest("hex");
}

function mb(bytes) {
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function recoveryMessage() {
  return `Manual recovery command:\n${RECOVERY_COMMAND}`;
}

async function readPointer() {
  return JSON.parse(await readFile(pointerPath, "utf8"));
}

async function alreadyHydrated(pointer) {
  if (!existsSync(manifestPath)) {
    return false;
  }

  const data = await readFile(manifestPath);
  return sha256(data) === pointer.json_sha256;
}

async function hydrate() {
  const pointer = await readPointer();

  if (await alreadyHydrated(pointer)) {
    console.log("✓ manifest already hydrated");
    return;
  }

  const response = await fetch(pointer.asset_url);
  if (!response.ok) {
    throw new Error(`fetch failed: ${response.status} ${response.statusText}\n${recoveryMessage()}`);
  }

  const gzBytes = Buffer.from(await response.arrayBuffer());
  const actualGzSha = sha256(gzBytes);
  if (actualGzSha !== pointer.gz_sha256) {
    throw new Error(
      `gz sha256 mismatch: expected ${pointer.gz_sha256}, got ${actualGzSha}\n${recoveryMessage()}`,
    );
  }

  const jsonBytes = gunzipSync(gzBytes);
  const actualJsonSha = sha256(jsonBytes);
  if (actualJsonSha !== pointer.json_sha256) {
    throw new Error(
      `json sha256 mismatch after gunzip: expected ${pointer.json_sha256}, got ${actualJsonSha}\n${recoveryMessage()}`,
    );
  }

  await writeFile(tempPath, jsonBytes);
  await rename(tempPath, manifestPath);
  console.log(`hydrated ${mb(gzBytes.length)} gz -> ${mb(jsonBytes.length)} json`);
}

hydrate().catch(async (error) => {
  try {
    await unlink(tempPath);
  } catch {
    // Best effort cleanup; the failure above is the actionable error.
  }

  console.error(error instanceof Error ? error.message : String(error));
  console.error(recoveryMessage());
  process.exit(1);
});
