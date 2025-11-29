"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g = Object.create((typeof Iterator === "function" ? Iterator : Object).prototype);
    return g.next = verb(0), g["throw"] = verb(1), g["return"] = verb(2), typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
Object.defineProperty(exports, "__esModule", { value: true });
// scripts/generate-site.ts
var promises_1 = require("fs/promises");
var path_1 = require("path");
var CONTENT_DIR = 'course-content/l2-uk-en';
// Helper to extract title from markdown (first line # Title)
function getTitle(mdPath) {
    return __awaiter(this, void 0, void 0, function () {
        var content, match, e_1;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    _a.trys.push([0, 2, , 3]);
                    return [4 /*yield*/, (0, promises_1.readFile)(mdPath, 'utf-8')];
                case 1:
                    content = _a.sent();
                    match = content.match(/^# (.*)$/m);
                    return [2 /*return*/, match ? match[1].trim() : 'Untitled Module'];
                case 2:
                    e_1 = _a.sent();
                    return [2 /*return*/, 'Untitled Module'];
                case 3: return [2 /*return*/];
            }
        });
    });
}
function generateSite() {
    return __awaiter(this, void 0, void 0, function () {
        var books, entries, _i, entries_1, entry, bookId, bookPath, bookTitle, readme, match, e_2, moduleEntries, modules, _a, moduleEntries_1, modEntry, modPath, mdPath, title, indexHtml, allModulesFlat, _b, books_1, book, _c, _d, mod, relPath, i, current, prev, next, htmlPath, htmlContent, rootLink, navHtml, prevLink, nextLink, e_3;
        return __generator(this, function (_e) {
            switch (_e.label) {
                case 0:
                    console.log('Generating curriculum site...');
                    books = [];
                    return [4 /*yield*/, (0, promises_1.readdir)(CONTENT_DIR, { withFileTypes: true })];
                case 1:
                    entries = _e.sent();
                    _i = 0, entries_1 = entries;
                    _e.label = 2;
                case 2:
                    if (!(_i < entries_1.length)) return [3 /*break*/, 13];
                    entry = entries_1[_i];
                    if (!(entry.isDirectory() && entry.name.startsWith('book-'))) return [3 /*break*/, 12];
                    bookId = entry.name;
                    bookPath = (0, path_1.join)(CONTENT_DIR, bookId);
                    bookTitle = bookId.replace(/-/g, ' ').toUpperCase();
                    _e.label = 3;
                case 3:
                    _e.trys.push([3, 5, , 6]);
                    return [4 /*yield*/, (0, promises_1.readFile)((0, path_1.join)(bookPath, 'README.md'), 'utf-8')];
                case 4:
                    readme = _e.sent();
                    match = readme.match(/^# (.*)$/m);
                    if (match)
                        bookTitle = match[1];
                    return [3 /*break*/, 6];
                case 5:
                    e_2 = _e.sent();
                    return [3 /*break*/, 6];
                case 6: return [4 /*yield*/, (0, promises_1.readdir)(bookPath, { withFileTypes: true })];
                case 7:
                    moduleEntries = _e.sent();
                    modules = [];
                    _a = 0, moduleEntries_1 = moduleEntries;
                    _e.label = 8;
                case 8:
                    if (!(_a < moduleEntries_1.length)) return [3 /*break*/, 11];
                    modEntry = moduleEntries_1[_a];
                    if (!(modEntry.isDirectory() && modEntry.name.startsWith('module-'))) return [3 /*break*/, 10];
                    modPath = (0, path_1.join)(bookPath, modEntry.name);
                    mdPath = (0, path_1.join)(modPath, 'textbook.md');
                    return [4 /*yield*/, getTitle(mdPath)];
                case 9:
                    title = _e.sent();
                    modules.push({
                        id: modEntry.name,
                        title: title,
                        path: modPath,
                        book: bookId
                    });
                    _e.label = 10;
                case 10:
                    _a++;
                    return [3 /*break*/, 8];
                case 11:
                    // Sort modules by name (module-01, module-02...)
                    modules.sort(function (a, b) { return a.id.localeCompare(b.id); });
                    books.push({ id: bookId, title: bookTitle, modules: modules });
                    _e.label = 12;
                case 12:
                    _i++;
                    return [3 /*break*/, 2];
                case 13:
                    // Sort books
                    books.sort(function (a, b) { return a.id.localeCompare(b.id); });
                    indexHtml = "\n<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n  <meta charset=\"UTF-8\">\n  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n  <title>Neural Dojo: Ukrainian L2 Curriculum</title>\n  <style>\n    body { font-family: system-ui, sans-serif; line-height: 1.6; max-width: 900px; margin: 0 auto; padding: 2rem; background: #f4f4f9; color: #333; }\n    h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 0.5rem; }\n    .book-card { background: white; padding: 1.5rem; margin-bottom: 2rem; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }\n    .book-title { color: #e67e22; margin-top: 0; }\n    .module-list { list-style: none; padding: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 1rem; }\n    .module-item a { display: block; padding: 10px; background: #ecf0f1; color: #2c3e50; text-decoration: none; border-radius: 4px; transition: 0.2s; }\n    .module-item a:hover { background: #3498db; color: white; }\n    .badge { font-size: 0.8em; background: #95a5a6; color: white; padding: 2px 6px; border-radius: 4px; float: right; }\n  </style>\n</head>\n<body>\n  <h1>\uD83C\uDDFA\uD83C\uDDE6 Neural Dojo: Ukrainian L2 Curriculum</h1>\n  <p>A theory-first, vocabulary-rich path from A1 to C1.</p>\n";
                    allModulesFlat = [];
                    for (_b = 0, books_1 = books; _b < books_1.length; _b++) {
                        book = books_1[_b];
                        indexHtml += "<div class=\"book-card\"><h2 class=\"book-title\">".concat(book.title, "</h2><ul class=\"module-list\">");
                        for (_c = 0, _d = book.modules; _c < _d.length; _c++) {
                            mod = _d[_c];
                            allModulesFlat.push(mod);
                            relPath = "".concat(book.id, "/").concat(mod.id, "/textbook.html");
                            indexHtml += "<li class=\"module-item\"><a href=\"".concat(relPath, "\">").concat(mod.title, "</a></li>");
                        }
                        indexHtml += "</ul></div>";
                    }
                    indexHtml += "</body></html>";
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(CONTENT_DIR, 'index.html'), indexHtml)];
                case 14:
                    _e.sent();
                    console.log("Generated Index: ".concat((0, path_1.join)(CONTENT_DIR, 'index.html')));
                    i = 0;
                    _e.label = 15;
                case 15:
                    if (!(i < allModulesFlat.length)) return [3 /*break*/, 22];
                    current = allModulesFlat[i];
                    prev = i > 0 ? allModulesFlat[i - 1] : null;
                    next = i < allModulesFlat.length - 1 ? allModulesFlat[i + 1] : null;
                    htmlPath = (0, path_1.join)(current.path, 'textbook.html');
                    _e.label = 16;
                case 16:
                    _e.trys.push([16, 20, , 21]);
                    return [4 /*yield*/, (0, promises_1.readFile)(htmlPath, 'utf-8')];
                case 17:
                    htmlContent = _e.sent();
                    rootLink = '../../index.html';
                    navHtml = "<div style=\"background: #2c3e50; padding: 1rem; margin: -2rem -2rem 2rem -2rem; display: flex; justify-content: space-between; align-items: center; color: white;\">";
                    // Prev Button
                    if (prev) {
                        prevLink = "../../".concat(prev.book, "/").concat(prev.id, "/textbook.html");
                        navHtml += "<a href=\"".concat(prevLink, "\" style=\"color: white; text-decoration: none;\">\u2190 ").concat(prev.title, "</a>");
                    }
                    else {
                        navHtml += "<span></span>";
                    }
                    // Home Button
                    navHtml += "<a href=\"".concat(rootLink, "\" style=\"color: white; font-weight: bold; text-decoration: none;\">\uD83C\uDFE0 Curriculum Home</a>");
                    // Next Button
                    if (next) {
                        nextLink = "../../".concat(next.book, "/").concat(next.id, "/textbook.html");
                        navHtml += "<a href=\"".concat(nextLink, "\" style=\"color: white; text-decoration: none;\">").concat(next.title, " \u2192</a>");
                    }
                    else {
                        navHtml += "<span></span>";
                    }
                    navHtml += "</div>";
                    if (!!htmlContent.includes('Curriculum Home')) return [3 /*break*/, 19];
                    htmlContent = htmlContent.replace('<body>', '<body>' + navHtml);
                    // Add bottom nav too
                    htmlContent = htmlContent.replace('</body>', navHtml + '</body>');
                    return [4 /*yield*/, (0, promises_1.writeFile)(htmlPath, htmlContent)];
                case 18:
                    _e.sent();
                    console.log("Updated Nav: ".concat(current.id));
                    _e.label = 19;
                case 19: return [3 /*break*/, 21];
                case 20:
                    e_3 = _e.sent();
                    return [3 /*break*/, 21];
                case 21:
                    i++;
                    return [3 /*break*/, 15];
                case 22: return [2 /*return*/];
            }
        });
    });
}
generateSite().catch(console.error);
