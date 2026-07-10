import { existsSync } from "node:fs";
import { readFile, rename, unlink, writeFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { gunzipSync } from "node:zlib";

const RECOVERY_COMMAND =
  "gh release download atlas-manifest -p lexicon-manifest.json.gz -O - | gunzip -c > site/src/data/lexicon-manifest.json";
const STALE_POINTER_HINT =
  "If your branch predates the latest manifest publish, its committed pointer is stale — update the branch from origin/main (gh pr update-branch <N> / git merge origin/main). Re-downloading cannot fix a stale pointer.";

const REQUIRED_POINTER_KEYS = [
  "asset_url",
  "release_tag",
  "manifest_version",
  "manifest_fingerprint",
  "fingerprint_schema_version",
  "gz_sha256",
  "json_sha256",
  "gz_bytes",
  "json_bytes",
];

const scriptDir = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(scriptDir, "../..");
const pointerPath = resolve(repoRoot, "site/src/data/lexicon-manifest.pointer.json");
const fingerprintPath = resolve(repoRoot, "site/src/data/lexicon-manifest.fingerprint.json");
const manifestPath = resolve(repoRoot, "site/src/data/lexicon-manifest.json");
const tempPath = `${manifestPath}.tmp`;
const allowStalePointer = process.env.ATLAS_MANIFEST_ALLOW_STALE_POINTER === "1";
const DOWNLOAD_ATTEMPTS = 3;

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

function assertPointerFresh(pointer, fingerprint) {
  if (allowStalePointer) return;

  const missing = REQUIRED_POINTER_KEYS.filter((key) => pointer[key] === undefined || pointer[key] === null || pointer[key] === "");
  if (missing.length > 0) {
    throw new Error(
      `Atlas manifest pointer missing freshness keys: ${missing.join(", ")}. Run make atlas-publish.`,
    );
  }

  if (pointer.fingerprint_schema_version !== fingerprint.schema_version) {
    throw new Error(
      `Atlas manifest pointer schema ${pointer.fingerprint_schema_version} is stale; expected ${fingerprint.schema_version}. Run make atlas-publish.`,
    );
  }

  if (pointer.manifest_fingerprint !== fingerprint.fingerprint) {
    console.warn(
      `Atlas manifest pointer fingerprint ${pointer.manifest_fingerprint} is stale; expected ${fingerprint.fingerprint}. Run make atlas-publish.`,
    );
  }
}

function assertManifestFresh(manifest, pointer, sourceLabel) {
  if (allowStalePointer) return;

  if (manifest.version !== pointer.manifest_version) {
    throw new Error(
      `${sourceLabel} manifest version ${manifest.version ?? "<missing>"} does not match pointer ${pointer.manifest_version}. Run make atlas-publish.`,
    );
  }

  const embedded = manifest.manifest_fingerprint;
  if (!embedded || typeof embedded !== "object") {
    throw new Error(`${sourceLabel} lacks manifest_fingerprint. Run make atlas-publish.`);
  }

  if (embedded.schema_version !== pointer.fingerprint_schema_version) {
    throw new Error(
      `${sourceLabel} fingerprint schema ${embedded.schema_version ?? "<missing>"} does not match pointer ${pointer.fingerprint_schema_version}. Run make atlas-publish.`,
    );
  }

  if (embedded.fingerprint !== pointer.manifest_fingerprint) {
    throw new Error(
      `${sourceLabel} fingerprint ${embedded.fingerprint ?? "<missing>"} does not match pointer ${pointer.manifest_fingerprint}. Run make atlas-publish.`,
    );
  }
}

function parseManifest(jsonBytes, pointer, sourceLabel) {
  const manifest = JSON.parse(jsonBytes.toString("utf8"));
  assertManifestFresh(manifest, pointer, sourceLabel);
  return manifest;
}

// The manifest pointer is a trusted, fingerprint-gated, committed artifact, but
// the download target it carries still flows from file data into an outbound
// request. Allowlist the origin so a tampered/misgenerated pointer cannot
// redirect the fetch to an arbitrary host — or to an attacker-controlled GitHub
// release — before the bytes are sha256-verified (supply-chain defense; CodeQL
// #251). The pointer always names this repo's release asset on github.com; the
// fetch then transparently 302s to GitHub's opaque *.githubusercontent.com CDN.
const ALLOWED_RELEASE_PATH_PREFIX =
  "/learn-ukrainian/learn-ukrainian.github.io/releases/download/";

function assertAllowedDownloadUrl(rawUrl) {
  let parsed;
  try {
    parsed = new URL(rawUrl);
  } catch {
    throw new Error(`Atlas manifest asset_url is not a valid URL: ${rawUrl}`);
  }
  if (parsed.protocol !== "https:") {
    throw new Error(`Atlas manifest asset_url must use https, got ${parsed.protocol} (${rawUrl})`);
  }
  const host = parsed.hostname.toLowerCase();
  // github.com targets must point at THIS repo's releases (not just any GitHub
  // account); *.githubusercontent.com are GitHub-controlled redirect/CDN hosts
  // with opaque paths, so they are validated by host only.
  const fromRepoRelease = host === "github.com" && parsed.pathname.startsWith(ALLOWED_RELEASE_PATH_PREFIX);
  const fromGithubCdn = host.endsWith(".githubusercontent.com");
  if (!fromRepoRelease && !fromGithubCdn) {
    throw new Error(
      `Atlas manifest asset_url is not an allowlisted GitHub release URL: ${rawUrl}. ` +
        `Expected https://github.com${ALLOWED_RELEASE_PATH_PREFIX}* or https://*.githubusercontent.com/*.`,
    );
  }
  return parsed.toString();
}

function downloadUrl(pointer, attempt) {
  if (attempt === 0) return pointer.asset_url;

  const url = new URL(pointer.asset_url);
  url.searchParams.set("atlas_manifest_sha256", pointer.gz_sha256);
  url.searchParams.set("atlas_manifest_attempt", String(attempt));
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
          "User-Agent": "learn-ukrainian-atlas-manifest-hydrate/1.0",
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
      `failed to download Atlas manifest release asset after ${DOWNLOAD_ATTEMPTS} attempts: ${message}\n${recoveryMessage()}`,
    );
  }

  throw new Error(
    `gz sha mismatch: expected ${pointer.gz_sha256}, got ${actualGzSha} after ${DOWNLOAD_ATTEMPTS} download attempts. ${STALE_POINTER_HINT}`,
  );
}

async function alreadyHydrated(pointer) {
  if (!existsSync(manifestPath)) return false;

  const data = await readFile(manifestPath);
  if (sha256(data) !== pointer.json_sha256) return false;

  parseManifest(data, pointer, manifestPath);
  return true;
}

// Local-work guard (#4917 incident, 2026-07-10): during an intake arc the local
// manifest legitimately carries MORE entries than the latest published release
// (promote/enrich run locally BEFORE `make atlas-publish` ships the new asset).
// A site build running `npm run hydrate` in that window used to silently
// overwrite the richer local manifest with the older published one — wiping an
// in-flight promotion (2,919 promoted + enriched entries lost). Refuse by
// default; force only via ATLAS_MANIFEST_FORCE_HYDRATE=1 (explicit restore).
async function assertNotClobberingRicherLocal(downloadedEntryCount, localPath = manifestPath) {
  if (process.env.ATLAS_MANIFEST_FORCE_HYDRATE === "1" || !existsSync(localPath)) return;

  let localEntryCount = null;
  try {
    const local = JSON.parse(await readFile(localPath, "utf8"));
    if (Array.isArray(local.entries)) localEntryCount = local.entries.length;
  } catch {
    return; // unreadable/corrupt local file → replacing it is an improvement
  }

  if (localEntryCount !== null && localEntryCount > downloadedEntryCount) {
    throw new Error(
      `refusing to overwrite local manifest with ${localEntryCount} entries using the ` +
        `published release with only ${downloadedEntryCount} — the local file looks like ` +
        `in-flight intake work (promote/enrich before publish). Publish it with ` +
        `make atlas-publish, or force the restore with ATLAS_MANIFEST_FORCE_HYDRATE=1.`,
    );
  }
}

async function hydrate() {
  const [pointer, fingerprint] = await Promise.all([readJson(pointerPath), readJson(fingerprintPath)]);
  assertPointerFresh(pointer, fingerprint);

  if (await alreadyHydrated(pointer)) {
    console.log("✓ manifest already hydrated");
    return;
  }

  const gzBytes = await downloadGzip(pointer);
  if (gzBytes.length !== pointer.gz_bytes) {
    throw new Error(`gz size mismatch: expected ${pointer.gz_bytes}, got ${gzBytes.length}`);
  }

  const jsonBytes = gunzipSync(gzBytes);
  const actualJsonSha = sha256(jsonBytes);
  if (actualJsonSha !== pointer.json_sha256) {
    throw new Error(
      `json sha mismatch: expected ${pointer.json_sha256}, got ${actualJsonSha}. ${STALE_POINTER_HINT}`,
    );
  }
  if (jsonBytes.length !== pointer.json_bytes) {
    throw new Error(`json size mismatch: expected ${pointer.json_bytes}, got ${jsonBytes.length}`);
  }

  const downloaded = parseManifest(jsonBytes, pointer, pointer.asset_url);
  const downloadedEntryCount = Array.isArray(downloaded.entries) ? downloaded.entries.length : 0;
  await assertNotClobberingRicherLocal(downloadedEntryCount);
  await writeFile(tempPath, jsonBytes);
  await rename(tempPath, manifestPath);
  console.log(`✓ hydrated manifest ${mb(jsonBytes.length)} from ${mb(gzBytes.length)} release asset`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  hydrate().catch(async (error) => {
    await unlink(tempPath).catch(() => {});
    console.error(`Failed to hydrate lexicon manifest: ${error.message}`);
    process.exit(1);
  });
}

export {
  assertAllowedDownloadUrl,
  assertNotClobberingRicherLocal,
  assertPointerFresh,
  downloadGzip,
  downloadUrl,
};
