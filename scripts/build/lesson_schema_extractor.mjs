#!/usr/bin/env node
import ts from "typescript";
import { readFileSync } from "node:fs";
import { basename } from "node:path";
function tags(node) {
  const out = {};
  for (const tag of ts.getJSDocTags(node)) {
    const name = tag.tagName.escapedText.toString();
    out[name] = (tag.comment ?? "").toString().trim();
  }
  return out;
}
function cleanType(typeNode, source) {
  if (!typeNode) return "unknown";
  return typeNode.getText(source).replace(/\s+/g, " ").trim();
}
function readInterface(node, source) {
  return {
    name: node.name.escapedText.toString(),
    tags: tags(node),
    props: node.members
      .filter((member) => ts.isPropertySignature(member))
      .map((member) => ({
        name: member.name.getText(source),
        optional: Boolean(member.questionToken),
        type: cleanType(member.type, source),
        tags: tags(member),
      })),
  };
}
function extract(filePath) {
  const text = readFileSync(filePath, "utf8");
  const source = ts.createSourceFile(filePath, text, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  const interfaces = [];
  function visit(node) {
    if (ts.isInterfaceDeclaration(node)) interfaces.push(readInterface(node, source));
    ts.forEachChild(node, visit);
  }
  visit(source);
  return { path: filePath, component: basename(filePath).replace(/\.(tsx|astro)$/, ""), interfaces };
}
const files = process.argv.slice(2);
if (files.length === 0) {
  console.error("usage: lesson_schema_extractor.mjs <component.tsx> [...]");
  process.exit(2);
}
process.stdout.write(JSON.stringify(files.map(extract), null, 2));
