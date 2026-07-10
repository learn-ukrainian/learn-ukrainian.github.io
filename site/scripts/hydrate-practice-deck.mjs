import { existsSync } from "node:fs";
import { mkdir, readFile, rename, unlink, writeFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { gunzipSync } from "node:zlib";

const RECOVERY_COMMAND = "node site/scripts/hydrate-practice-deck.mjs";
const STALE_POINTER_HINT =
  "If your branch predates the latest practice deck publish, its committed pointer is stale — update the branch from origin/main (gh pr update-branch <N> / git merge origin/main). Re-downloading cannot fix a stale pointer.";

const REQUIRED_POINTER_KEYS = [
  "asset_url",
  "release_tag",
  "deck_version",
  "package_schema_version",
  "gz_sha256",
  "package_sha256",
  "gz_bytes",
  "package_bytes",
  "file_count",
  "files",
];

const scriptDir = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(scriptDir, "../..");
const pointerPath = resolve(repoRoot, "site/src/data/lexicon-practice-deck.pointer.json");
const practiceDir = resolve(repoRoot, "site/public/lexicon");
const DOWNLOAD_ATTEMPTS = 3;
const ALLOWED_RELEASE_PATH_PREFIX = "/learn-ukrainian/learn-ukrainian.github.io/releases/download/";
const SHARD_RE = /^practice-(index|lexemes|cloze|stress|classify|paradigm|synonym|heritage|paronym)\.(A1|A2|B1|B2|C1)\.json$/;

function sha256(data) {
  return createHash("sha256").update(data).digest("hex");
}

function mb(bytes) {
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function recoveryMessage() {
  return `Manual recovery command:\n${RECOVERY_COMMAND}`;
}

async function readJson(path) {
  return JSON.parse(await readFile(path, "utf8"));
}

function safeShardName(name) {
  if (typeof name !== "string" || !SHARD_RE.test(name) || name.includes("/") || name.includes("\\")) {
    throw new Error(`unsafe Atlas practice deck shard path: ${String(name)}`);
  }
  return name;
}

function assertPointerShape(pointer) {
  const missing = REQUIRED_POINTER_KEYS.filter((key) => !(key in pointer));
  if (missing.length > 0) {
    throw new Error(`Atlas practice deck pointer missing required keys: ${missing.join(", ")}`);
  }
  if (pointer.package_schema_version !== 1) {
    throw new Error(`Atlas practice deck package_schema_version must be 1`);
  }
  if (!Array.isArray(pointer.files) || pointer.files.length !== pointer.file_count) {
    throw new Error("Atlas practice deck pointer file_count does not match files");
  }
}

function pointerFiles(pointer) {
  const files = new Map();
  for (const rawFile of pointer.files) {
    const name = safeShardName(rawFile?.path);
    if (files.has(name)) {
      throw new Error(`duplicate Atlas practice deck pointer shard: ${name}`);
    }
    for (const key of ["sha256", "bytes", "level", "kind"]) {
      if (!(key in rawFile)) {
        throw new Error(`Atlas practice deck pointer shard ${name} missing ${key}`);
      }
    }
    files.set(name, rawFile);
  }
  return files;
}

function assertAllowedDownloadUrl(rawUrl) {
  let parsed;
  try {
    parsed = new URL(rawUrl);
  } catch {
    throw new Error(`Atlas practice deck asset_url is not valid URL: ${rawUrl}`);
  }
  if (parsed.protocol !== "https:") {
    throw new Error(`Atlas practice deck asset_url must use https, got ${parsed.protocol} (${rawUrl})`);
  }
  const host = parsed.hostname.toLowerCase();
  const fromRepoRelease = host === "github.com" && parsed.pathname.startsWith(ALLOWED_RELEASE_PATH_PREFIX);
  const fromGithubCdn = host.endsWith(".githubusercontent.com");
  if (!fromRepoRelease && !fromGithubCdn) {
    throw new Error(
      `Atlas practice deck asset_url is not allowlisted GitHub release URL: ${rawUrl}. ` +
        `Expected https://github.com${ALLOWED_RELEASE_PATH_PREFIX}* or https://*.githubusercontent.com/*.`,
    );
  }
  return parsed.toString();
}

function downloadUrl(pointer, attempt) {
  if (attempt === 0) return pointer.asset_url;
  const url = new URL(pointer.asset_url);
  url.searchParams.set("atlas_practice_deck_sha256", pointer.gz_sha256);
  url.searchParams.set("atlas_practice_deck_attempt", String(attempt));
  return url.toString();
}

async function downloadGzip(pointer) {
  let gzBytes = null;
  let actualGzSha = "";
  let lastError = null;
  let lastFailure = "";

  for (let attempt = 0; attempt < DOWNLOAD_ATTEMPTS; attempt += 1) {
    try {
      const requestUrl = assertAllowedDownloadUrl(downloadUrl(pointer, attempt));
      const response = await fetch(requestUrl, {
        cache: "no-store",
        headers: {
          Accept: "application/gzip, application/octet-stream;q=0.9, */*;q=0.1",
          "Cache-Control": "no-cache",
          Pragma: "no-cache",
          "User-Agent": "learn-ukrainian-atlas-practice-deck-hydrate/1.0",
        },
      });
      if (!response.ok) {
        throw new Error(`fetch failed: ${response.status} ${response.statusText}`);
      }
      gzBytes = Buffer.from(await response.arrayBuffer());
      actualGzSha = sha256(gzBytes);
      if (actualGzSha === pointer.gz_sha256) return gzBytes;
      lastFailure = "mismatch";
    } catch (error) {
      lastError = error;
      lastFailure = "error";
    }
  }

  if (lastError !== null && lastFailure === "error") {
    const message = lastError instanceof Error ? lastError.message : String(lastError);
    throw new Error(
      `failed to download Atlas practice deck release asset after ${DOWNLOAD_ATTEMPTS} attempts: ${message}\n${recoveryMessage()}`,
    );
  }
  throw new Error(
    `gz sha mismatch: expected ${pointer.gz_sha256}, got ${actualGzSha} after ${DOWNLOAD_ATTEMPTS} download attempts. ${STALE_POINTER_HINT}`,
  );
}

async function alreadyHydrated(pointer) {
  for (const [name, metadata] of pointerFiles(pointer)) {
    const path = resolve(practiceDir, name);
    if (!existsSync(path)) return false;
    const data = await readFile(path);
    if (data.length !== metadata.bytes || sha256(data) !== metadata.sha256) return false;
  }
  return true;
}

async function assertNotClobberingRicherLocal(pointer, localDir = practiceDir) {
  if (process.env.ATLAS_MANIFEST_FORCE_HYDRATE === "1") return;

  let localLexemeCount = 0;
  let releaseLexemeCount = 0;
  try {
    for (const [name, metadata] of pointerFiles(pointer)) {
      if (metadata.kind !== "index") continue;
      const releaseCount = metadata.counts?.lexemes;
      const local = JSON.parse(await readFile(resolve(localDir, name), "utf8"));
      const localCount = local?.counts?.lexemes;
      if (
        !Number.isInteger(releaseCount) || releaseCount < 0 ||
        !Number.isInteger(localCount) || localCount < 0
      ) return;
      releaseLexemeCount += releaseCount;
      localLexemeCount += localCount;
    }
  } catch {
    return; // missing or unreadable local shards may be replaced
  }

  if (localLexemeCount > releaseLexemeCount) {
    throw new Error(
      `refusing to overwrite local practice deck with ${localLexemeCount} lexemes using ` +
        `the published release with only ${releaseLexemeCount}. Publish it with make ` +
        `practice-deck-publish, or force the restore with ATLAS_MANIFEST_FORCE_HYDRATE=1.`,
    );
  }
}

function parsePackage(packageBytes, pointer) {
  if (packageBytes.length !== pointer.package_bytes) {
    throw new Error(`package size mismatch: expected ${pointer.package_bytes}, got ${packageBytes.length}`);
  }
  const actualPackageSha = sha256(packageBytes);
  if (actualPackageSha !== pointer.package_sha256) {
    throw new Error(`package sha mismatch: expected ${pointer.package_sha256}, got ${actualPackageSha}. ${STALE_POINTER_HINT}`);
  }
  const packagePayload = JSON.parse(packageBytes.toString("utf8"));
  if (packagePayload.schema !== "atlas-practice-deck-package") {
    throw new Error(`Atlas practice deck package schema mismatch`);
  }
  if (packagePayload.schemaVersion !== pointer.package_schema_version) {
    throw new Error(`Atlas practice deck package schemaVersion mismatch`);
  }
  if (packagePayload.deckVersion !== pointer.deck_version) {
    throw new Error(`Atlas practice deck package deckVersion mismatch`);
  }
  if (!Array.isArray(packagePayload.files) || packagePayload.files.length !== pointer.file_count) {
    throw new Error(`Atlas practice deck package file count mismatch`);
  }

  const pinnedFiles = pointerFiles(pointer);
  const seen = new Set();
  const hydratedFiles = [];
  for (const rawFile of packagePayload.files) {
    const name = safeShardName(rawFile?.path);
    if (seen.has(name)) {
      throw new Error(`duplicate Atlas practice deck package shard: ${name}`);
    }
    seen.add(name);
    if (!pinnedFiles.has(name)) {
      throw new Error(`Atlas practice deck package shard not pinned by pointer: ${name}`);
    }
    if (typeof rawFile.content !== "string") {
      throw new Error(`Atlas practice deck package shard ${name} missing string content`);
    }
    const data = Buffer.from(rawFile.content, "utf8");
    const metadata = pinnedFiles.get(name);
    if (data.length !== metadata.bytes || sha256(data) !== metadata.sha256) {
      throw new Error(`Atlas practice deck package shard hash mismatch: ${name}`);
    }
    hydratedFiles.push([name, data]);
  }
  if (seen.size !== pinnedFiles.size) {
    throw new Error(`Atlas practice deck package missing pointer-pinned shards`);
  }
  return hydratedFiles;
}

async function writeFiles(files) {
  await mkdir(practiceDir, { recursive: true });
  const tempPaths = [];
  try {
    for (const [name, data] of files) {
      const path = resolve(practiceDir, name);
      const tempPath = `${path}.tmp`;
      await writeFile(tempPath, data);
      tempPaths.push(tempPath);
    }
    for (const tempPath of tempPaths) {
      await rename(tempPath, tempPath.replace(/\.tmp$/, ""));
    }
  } finally {
    await Promise.all(tempPaths.map((path) => unlink(path).catch(() => {})));
  }
}

async function hydrate() {
  const pointer = await readJson(pointerPath);
  assertPointerShape(pointer);
  if (await alreadyHydrated(pointer)) {
    console.log("✓ practice deck already hydrated");
    return;
  }

  const gzBytes = await downloadGzip(pointer);
  if (gzBytes.length !== pointer.gz_bytes) {
    throw new Error(`gz size mismatch: expected ${pointer.gz_bytes}, got ${gzBytes.length}`);
  }
  const packageBytes = gunzipSync(gzBytes);
  const files = parsePackage(packageBytes, pointer);
  await assertNotClobberingRicherLocal(pointer);
  await writeFiles(files);
  console.log(`✓ hydrated practice deck ${pointer.deck_version} from ${mb(gzBytes.length)} release asset`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  hydrate().catch((error) => {
    console.error(`Failed to hydrate Atlas practice deck: ${error.message}`);
    process.exit(1);
  });
}

export { assertAllowedDownloadUrl, assertNotClobberingRicherLocal, downloadGzip, downloadUrl, parsePackage };
