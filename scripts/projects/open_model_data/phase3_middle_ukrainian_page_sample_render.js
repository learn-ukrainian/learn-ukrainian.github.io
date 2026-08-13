#!/usr/bin/env node
"use strict";

/** Render exact full-resolution DjVu pages as private lossless PNG evidence. */

const crypto = require("crypto");
const fs = require("fs");
const path = require("path");
const zlib = require("zlib");

function fail(message) {
  throw new Error(message);
}

function parseArgs(argv) {
  const allowed = new Set([
    "--source",
    "--decoder",
    "--output-dir",
    "--pages",
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

function exactEmptyDirectory(directoryPath) {
  const metadata = fs.lstatSync(directoryPath);
  if (!metadata.isDirectory() || metadata.isSymbolicLink()) {
    fail("image output is not a non-symlink directory");
  }
  if (fs.readdirSync(directoryPath).length !== 0) fail("image output directory is not empty");
}

function parsePages(value, expectedPages) {
  if (!/^\d+(?:,\d+)*$/.test(value)) fail("invalid page selection");
  const pages = value.split(",").map(Number);
  if (
    pages.some((page) => !Number.isSafeInteger(page) || page < 1 || page > expectedPages)
    || pages.some((page, index) => index > 0 && page <= pages[index - 1])
  ) {
    fail("page selection must be strictly increasing and within the source denominator");
  }
  return pages;
}

function loadPinnedDecoder(decoderPath, expectedSha256, expectedVersion) {
  exactRegularFile(decoderPath, "decoder");
  const bytes = fs.readFileSync(decoderPath);
  if (sha256Buffer(bytes) !== expectedSha256) fail("decoder SHA-256 drift");

  globalThis.ImageData = class ImageData {
    constructor(dataOrWidth, widthOrHeight, optionalHeight) {
      const fromPixelArray = dataOrWidth instanceof Uint8ClampedArray;
      const width = fromPixelArray ? widthOrHeight : dataOrWidth;
      const height = fromPixelArray
        ? (optionalHeight ?? (dataOrWidth.byteLength / (width * 4)))
        : widthOrHeight;
      if (!Number.isSafeInteger(width) || width <= 0 || !Number.isSafeInteger(height) || height <= 0) {
        fail("decoder requested invalid ImageData geometry");
      }
      this.width = width;
      this.height = height;
      if (fromPixelArray && dataOrWidth.byteLength !== width * height * 4) {
        fail("decoder requested invalid ImageData pixel length");
      }
      this.data = fromPixelArray ? dataOrWidth : new Uint8ClampedArray(width * height * 4);
    }
  };
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

const CRC_TABLE = (() => {
  const table = new Uint32Array(256);
  for (let value = 0; value < 256; value += 1) {
    let current = value;
    for (let bit = 0; bit < 8; bit += 1) {
      current = (current & 1) ? (0xedb88320 ^ (current >>> 1)) : (current >>> 1);
    }
    table[value] = current >>> 0;
  }
  return table;
})();

function crc32(buffer) {
  let crc = 0xffffffff;
  for (const byte of buffer) crc = CRC_TABLE[(crc ^ byte) & 0xff] ^ (crc >>> 8);
  return (crc ^ 0xffffffff) >>> 0;
}

function pngChunk(type, data) {
  const typeBuffer = Buffer.from(type, "ascii");
  const chunk = Buffer.allocUnsafe(12 + data.length);
  chunk.writeUInt32BE(data.length, 0);
  typeBuffer.copy(chunk, 4);
  data.copy(chunk, 8);
  chunk.writeUInt32BE(crc32(Buffer.concat([typeBuffer, data])), 8 + data.length);
  return chunk;
}

function encodeRgbaPng(imageData) {
  const { width, height, data } = imageData;
  if (!Number.isSafeInteger(width) || width <= 0 || !Number.isSafeInteger(height) || height <= 0) {
    fail("rendered page has invalid dimensions");
  }
  if (!(data instanceof Uint8ClampedArray) || data.byteLength !== width * height * 4) {
    fail("rendered page has invalid RGBA data");
  }
  const rowBytes = width * 4;
  const scanlines = Buffer.allocUnsafe(height * (rowBytes + 1));
  const rgba = Buffer.from(data.buffer, data.byteOffset, data.byteLength);
  for (let row = 0; row < height; row += 1) {
    const outputOffset = row * (rowBytes + 1);
    scanlines[outputOffset] = 0;
    rgba.copy(scanlines, outputOffset + 1, row * rowBytes, (row + 1) * rowBytes);
  }
  const header = Buffer.alloc(13);
  header.writeUInt32BE(width, 0);
  header.writeUInt32BE(height, 4);
  header[8] = 8;
  header[9] = 6;
  header[10] = 0;
  header[11] = 0;
  header[12] = 0;
  return {
    png: Buffer.concat([
      Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]),
      pngChunk("IHDR", header),
      pngChunk("IDAT", zlib.deflateSync(scanlines, { level: 9 })),
      pngChunk("IEND", Buffer.alloc(0)),
    ]),
    rgba,
  };
}

function run() {
  const args = parseArgs(process.argv.slice(2));
  const sourcePath = path.resolve(args["--source"]);
  const decoderPath = path.resolve(args["--decoder"]);
  const outputDirectory = path.resolve(args["--output-dir"]);
  const expectedSourceBytes = Number(args["--expected-source-bytes"]);
  const expectedPages = Number(args["--expected-pages"]);
  if (!Number.isSafeInteger(expectedSourceBytes) || expectedSourceBytes <= 0) fail("invalid expected source bytes");
  if (!Number.isSafeInteger(expectedPages) || expectedPages <= 0) fail("invalid expected page count");
  const pages = parsePages(args["--pages"], expectedPages);
  exactEmptyDirectory(outputDirectory);

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

  const writtenPaths = [];
  const images = [];
  try {
    for (const pageNumber of pages) {
      const page = document.getPageUnsafe(pageNumber);
      try {
        const expectedWidth = page.getWidth();
        const expectedHeight = page.getHeight();
        const expectedDpi = page.getDpi();
        const expectedRotation = page.getRotation();
        const imageData = page.getImageData();
        if (imageData.width !== expectedWidth || imageData.height !== expectedHeight) {
          fail(`page ${pageNumber} rendered geometry drift`);
        }
        const { png, rgba } = encodeRgbaPng(imageData);
        const filename = `page-${String(pageNumber).padStart(3, "0")}.png`;
        const outputPath = path.join(outputDirectory, filename);
        writtenPaths.push(outputPath);
        fs.writeFileSync(outputPath, png, { flag: "wx", mode: 0o600 });
        images.push({
          page_number: pageNumber,
          filename,
          width: imageData.width,
          height: imageData.height,
          dpi: expectedDpi,
          rotation: expectedRotation,
          rgba_bytes: rgba.byteLength,
          rgba_sha256: sha256Buffer(rgba),
          png_bytes: png.byteLength,
          png_sha256: sha256Buffer(png),
        });
      } finally {
        page.reset();
      }
    }
  } catch (error) {
    for (const outputPath of writtenPaths) {
      try {
        fs.unlinkSync(outputPath);
      } catch (_cleanupError) {}
    }
    throw error;
  }

  process.stdout.write(`${JSON.stringify({
    source_sha256: sourceSha256,
    decoder_version: decoder.VERSION,
    node_version: process.version,
    zlib_version: process.versions.zlib,
    page_selection: pages,
    images,
    image_count: images.length,
    total_png_bytes: images.reduce((total, image) => total + image.png_bytes, 0),
    provider_calls: false,
  })}\n`);
}

try {
  run();
} catch (error) {
  process.stderr.write(`phase3_middle_ukrainian_page_sample_render: ${error.message}\n`);
  process.exitCode = 2;
}
