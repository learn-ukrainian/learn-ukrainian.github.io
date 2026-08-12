#!/usr/bin/env node
"use strict";

/**
 * Decode the embedded DjVu text layer into page-aligned private JSONL.
 *
 * This runner is intentionally generic and receives all immutable identities
 * from the Python controller. It never downloads a decoder or source, performs
 * OCR, normalizes text, repairs characters, or writes a public artifact.
 */

const crypto = require("crypto");
const fs = require("fs");
const path = require("path");

const ROW_SCHEMA_VERSION = "phase3_middle_ukrainian_page_text_private_v1";

function fail(message) {
  throw new Error(message);
}

function parseArgs(argv) {
  const allowed = new Set([
    "--source",
    "--decoder",
    "--output",
    "--expected-source-sha256",
    "--expected-source-bytes",
    "--expected-decoder-sha256",
    "--expected-decoder-version",
    "--expected-pages",
  ]);
  const values = {};
  for (let index = 0; index < argv.length; index += 2) {
    const key = argv[index];
    const value = argv[index + 1];
    if (!allowed.has(key) || value === undefined || values[key] !== undefined) {
      fail(`invalid or duplicated argument: ${key || "<missing>"}`);
    }
    values[key] = value;
  }
  for (const key of allowed) {
    if (values[key] === undefined) fail(`missing required argument: ${key}`);
  }
  return values;
}

function sha256Buffer(value) {
  return crypto.createHash("sha256").update(value).digest("hex");
}

function exactRegularFile(filePath, label) {
  const metadata = fs.lstatSync(filePath);
  if (!metadata.isFile() || metadata.isSymbolicLink()) {
    fail(`${label} is not a regular non-symlink file`);
  }
  return metadata;
}

function loadPinnedDecoder(decoderPath, expectedSha256, expectedVersion) {
  exactRegularFile(decoderPath, "decoder");
  const bytes = fs.readFileSync(decoderPath);
  if (sha256Buffer(bytes) !== expectedSha256) fail("decoder SHA-256 drift");

  // Node 25 exposes a warning-producing localStorage getter. DjVu.js does not
  // need persistence for synchronous document/text decoding, so provide the
  // smallest inert browser-compatible surface before evaluating pinned code.
  Object.defineProperty(globalThis, "localStorage", {
    configurable: true,
    value: {
      getItem() {
        return null;
      },
      removeItem() {},
      setItem() {},
    },
  });

  const decoderSource = bytes.toString("utf8");
  const load = new Function("self", `${decoderSource}\n; return DjVu;`);
  const decoder = load({ document: {} });
  if (!decoder || typeof decoder.Document !== "function") fail("decoder API is missing Document");
  if (decoder.VERSION !== expectedVersion) fail("decoder version drift");
  return decoder;
}

function validateGeometry(pageNumber, width, height, dpi, rotation) {
  if (![width, height, dpi].every((value) => Number.isInteger(value) && value > 0)) {
    fail(`page ${pageNumber} has invalid dimensions or DPI`);
  }
  if (![0, 90, 180, 270].includes(rotation)) fail(`page ${pageNumber} has invalid rotation`);
}

function normalizeZones(pageNumber, zones, width, height) {
  if (zones === null) return null;
  if (!Array.isArray(zones)) fail(`page ${pageNumber} text zones are not an array or null`);
  return zones.map((zone, zoneIndex) => {
    const values = [zone.x, zone.y, zone.width, zone.height];
    if (!values.every((value) => Number.isInteger(value) && value >= 0)) {
      fail(`page ${pageNumber} zone ${zoneIndex} has invalid geometry`);
    }
    if (zone.x + zone.width > width || zone.y + zone.height > height) {
      fail(`page ${pageNumber} zone ${zoneIndex} exceeds page bounds`);
    }
    if (typeof zone.text !== "string") fail(`page ${pageNumber} zone ${zoneIndex} text is not a string`);
    return {
      x: zone.x,
      y: zone.y,
      width: zone.width,
      height: zone.height,
      text: zone.text,
    };
  });
}

function run() {
  const args = parseArgs(process.argv.slice(2));
  const sourcePath = path.resolve(args["--source"]);
  const decoderPath = path.resolve(args["--decoder"]);
  const outputPath = path.resolve(args["--output"]);
  const expectedSourceBytes = Number(args["--expected-source-bytes"]);
  const expectedPages = Number(args["--expected-pages"]);
  if (!Number.isSafeInteger(expectedSourceBytes) || expectedSourceBytes <= 0) fail("invalid expected source bytes");
  if (!Number.isSafeInteger(expectedPages) || expectedPages <= 0) fail("invalid expected page count");

  const sourceMetadata = exactRegularFile(sourcePath, "source");
  if (sourceMetadata.size !== expectedSourceBytes) fail("source byte count drift");
  const sourceBytes = fs.readFileSync(sourcePath);
  const sourceSha256 = sha256Buffer(sourceBytes);
  if (sourceSha256 !== args["--expected-source-sha256"]) fail("source SHA-256 drift");

  const decoder = loadPinnedDecoder(
    decoderPath,
    args["--expected-decoder-sha256"],
    args["--expected-decoder-version"],
  );
  const arrayBuffer = sourceBytes.buffer.slice(
    sourceBytes.byteOffset,
    sourceBytes.byteOffset + sourceBytes.byteLength,
  );
  const document = new decoder.Document(arrayBuffer);
  if (document.getPagesQuantity() !== expectedPages) fail("decoder page denominator drift");
  if (fs.existsSync(outputPath)) fail("private JSONL output already exists");

  let outputHandle = null;
  const outputDigest = crypto.createHash("sha256");
  const textHashes = [];
  const zoneHashes = [];
  const geometryManifest = [];
  let outputBytes = 0;
  let textLayerPages = 0;
  let nonemptyTextPages = 0;
  let totalCodePoints = 0;
  let totalUtf8Bytes = 0;
  let totalZones = 0;
  try {
    outputHandle = fs.openSync(outputPath, "wx", 0o600);
    for (let pageNumber = 1; pageNumber <= expectedPages; pageNumber += 1) {
      const page = document.getPageUnsafe(pageNumber);
      try {
        const width = page.getWidth();
        const height = page.getHeight();
        const dpi = page.getDpi();
        const rotation = page.getRotation();
        validateGeometry(pageNumber, width, height, dpi, rotation);

        const decodedText = page.getText();
        if (typeof decodedText !== "string") fail(`page ${pageNumber} decoded text is not a string`);
        const textZones = normalizeZones(
          pageNumber,
          page.getNormalizedTextZones(),
          width,
          height,
        );
        const textLayerPresent = textZones !== null;
        const decodedTextSha256 = sha256Buffer(Buffer.from(decodedText, "utf8"));
        const textZonesSha256 = sha256Buffer(Buffer.from(JSON.stringify(textZones), "utf8"));
        const decodedTextCodePoints = Array.from(decodedText).length;
        const decodedTextUtf8Bytes = Buffer.byteLength(decodedText, "utf8");
        const zoneCount = textZones === null ? 0 : textZones.length;

        const row = {
          schema_version: ROW_SCHEMA_VERSION,
          source_sha256: sourceSha256,
          page_number: pageNumber,
          page_width: width,
          page_height: height,
          dpi,
          rotation,
          text_layer_present: textLayerPresent,
          decoded_text: decodedText,
          decoded_text_sha256: decodedTextSha256,
          decoded_text_code_points: decodedTextCodePoints,
          decoded_text_utf8_bytes: decodedTextUtf8Bytes,
          text_zones: textZones,
          text_zones_sha256: textZonesSha256,
          text_zone_count: zoneCount,
          ocr_used: false,
          normalization_applied: false,
          inferred_character_repairs: false,
        };
        const line = `${JSON.stringify(row)}\n`;
        fs.writeSync(outputHandle, line, null, "utf8");
        outputDigest.update(line, "utf8");
        outputBytes += Buffer.byteLength(line, "utf8");
        textHashes.push(decodedTextSha256);
        zoneHashes.push(textZonesSha256);
        geometryManifest.push({ page_number: pageNumber, width, height, dpi, rotation });
        if (textLayerPresent) textLayerPages += 1;
        if (decodedText.length > 0) nonemptyTextPages += 1;
        totalCodePoints += decodedTextCodePoints;
        totalUtf8Bytes += decodedTextUtf8Bytes;
        totalZones += zoneCount;
      } finally {
        page.reset();
      }
    }
    fs.closeSync(outputHandle);
    outputHandle = null;
  } catch (error) {
    if (outputHandle !== null) fs.closeSync(outputHandle);
    if (fs.existsSync(outputPath)) fs.unlinkSync(outputPath);
    throw error;
  }

  const summary = {
    row_schema_version: ROW_SCHEMA_VERSION,
    decoder_version: decoder.VERSION,
    source_sha256: sourceSha256,
    pages: expectedPages,
    text_layer_pages: textLayerPages,
    nonempty_text_pages: nonemptyTextPages,
    total_code_points: totalCodePoints,
    total_utf8_bytes: totalUtf8Bytes,
    total_zones: totalZones,
    private_jsonl_bytes: outputBytes,
    private_jsonl_sha256: outputDigest.digest("hex"),
    page_text_hash_manifest_sha256: sha256Buffer(Buffer.from(JSON.stringify(textHashes), "utf8")),
    text_zone_hash_manifest_sha256: sha256Buffer(Buffer.from(JSON.stringify(zoneHashes), "utf8")),
    page_geometry_manifest_sha256: sha256Buffer(
      Buffer.from(JSON.stringify(geometryManifest), "utf8"),
    ),
    ocr_used: false,
    normalization_applied: false,
    inferred_character_repairs: false,
  };
  process.stdout.write(`${JSON.stringify(summary)}\n`);
}

try {
  run();
} catch (error) {
  process.stderr.write(`phase3_middle_ukrainian_djvu_extract: ${error.message}\n`);
  process.exitCode = 2;
}
