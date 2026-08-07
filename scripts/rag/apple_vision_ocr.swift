import CoreGraphics
import Darwin
import Foundation
import PDFKit
import Vision

private let schemaVersion = "apple-vision-ocr.v1"
private let helperVersion = "apple-vision-ocr.swift.v1"

private struct RuntimeMetadata: Codable {
    let helper_version: String
    let os_version: String
    let swift_language_version: String
}

private struct RecognizerMetadata: Codable {
    let framework: String
    let request: String
    let recognition_languages: [String]
    let recognition_level: String
    let uses_cpu_only: Bool
    let revision: Int
}

private struct OCRMetadata: Codable {
    let runtime: RuntimeMetadata
    let recognizer: RecognizerMetadata
}

private struct OCRPage: Codable {
    let page_number: Int
    let text: String
    let observation_count: Int
    let mean_confidence: Double
    let line_break_count: Int
}

private struct OCRResponse: Codable {
    let schema_version: String
    let metadata: OCRMetadata
    let pages: [OCRPage]
}

private struct OrderedObservation {
    let text: String
    let confidence: Float
    let box: CGRect
}

private enum OCRFailure: LocalizedError {
    case usage(String)
    case invalidPage(String)
    case unreadablePDF
    case missingPage(Int)
    case renderFailure(Int)

    var errorDescription: String? {
        switch self {
        case .usage(let message):
            return message
        case .invalidPage(let message):
            return message
        case .unreadablePDF:
            return "Could not open the PDF with PDFKit"
        case .missingPage(let page):
            return "PDF has no requested page \(page)"
        case .renderFailure(let page):
            return "Could not render PDF page \(page) in memory"
        }
    }
}

private func parseArguments() throws -> (URL, String, String) {
    var pdfPath: String?
    var pagesArgument: String?
    var mode = "ocr"
    var index = 1

    while index < CommandLine.arguments.count {
        let argument = CommandLine.arguments[index]
        switch argument {
        case "--pdf":
            index += 1
            guard index < CommandLine.arguments.count else {
                throw OCRFailure.usage("--pdf requires a path")
            }
            pdfPath = CommandLine.arguments[index]
        case "--pages":
            index += 1
            guard index < CommandLine.arguments.count else {
                throw OCRFailure.usage("--pages requires a comma-separated list")
            }
            pagesArgument = CommandLine.arguments[index]
        case "--mode":
            index += 1
            guard index < CommandLine.arguments.count else {
                throw OCRFailure.usage("--mode requires native or ocr")
            }
            mode = CommandLine.arguments[index]
        default:
            throw OCRFailure.usage("unknown argument \(argument)")
        }
        index += 1
    }

    guard let pdfPath, !pdfPath.isEmpty else {
        throw OCRFailure.usage("usage: apple_vision_ocr.swift --pdf PATH --pages 1,10")
    }
    guard let pagesArgument, !pagesArgument.isEmpty else {
        throw OCRFailure.usage("--pages is required; page numbers are one-based")
    }

    guard mode == "native" || mode == "ocr" else {
        throw OCRFailure.usage("--mode must be native or ocr")
    }
    return (URL(fileURLWithPath: pdfPath), pagesArgument, mode)
}

private func renderPage(_ page: PDFPage, pageNumber: Int) throws -> CGImage {
    let bounds = page.bounds(for: .mediaBox)
    // Textbook scans need enough raster detail for Ukrainian Cyrillic glyphs;
    // 2x produced pervasive Latin-lookalike substitutions in the live canary.
    let scale: CGFloat = 3.0
    let width = max(1, Int(ceil(bounds.width * scale)))
    let height = max(1, Int(ceil(bounds.height * scale)))
    let colorSpace = CGColorSpaceCreateDeviceRGB()
    guard let context = CGContext(
        data: nil,
        width: width,
        height: height,
        bitsPerComponent: 8,
        bytesPerRow: width * 4,
        space: colorSpace,
        bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
    ) else {
        throw OCRFailure.renderFailure(pageNumber)
    }

    context.setFillColor(CGColor(gray: 1.0, alpha: 1.0))
    context.fill(CGRect(x: 0, y: 0, width: width, height: height))
    context.saveGState()
    context.translateBy(x: 0, y: CGFloat(height))
    context.scaleBy(x: scale, y: -scale)
    page.draw(with: .mediaBox, to: context)
    context.restoreGState()

    guard let image = context.makeImage() else {
        throw OCRFailure.renderFailure(pageNumber)
    }
    return image
}

private func recognizePage(
    _ page: PDFPage,
    pageNumber: Int,
    requestRevision: Int
) throws -> OCRPage {
    let image = try renderPage(page, pageNumber: pageNumber)
    let handler = VNImageRequestHandler(cgImage: image, options: [:])
    let bandCount = 8
    let overlap: CGFloat = 0.015
    var allObservations: [OrderedObservation] = []
    var pageLines: [String] = []

    // Vision downsamples a full textbook page aggressively enough to miss
    // body text. Eight in-memory horizontal regions keep glyphs large for the
    // recognizer without writing page or tile images to disk.
    for band in 0..<bandCount {
        let bandHeight = 1.0 / CGFloat(bandCount)
        let coreY = 1.0 - CGFloat(band + 1) * bandHeight
        let y = max(0.0, coreY - overlap)
        let top = min(1.0, coreY + bandHeight + overlap)
        let request = VNRecognizeTextRequest()
        request.recognitionLevel = .accurate
        request.recognitionLanguages = ["uk-UA"]
        request.usesLanguageCorrection = true
        request.usesCPUOnly = true
        request.regionOfInterest = CGRect(x: 0.0, y: y, width: 1.0, height: top - y)
        try handler.perform([request])

        let observations: [OrderedObservation] = (request.results ?? []).compactMap { observation in
            guard let candidate = observation.topCandidates(1).first else {
                return nil
            }
            return OrderedObservation(
                text: candidate.string,
                confidence: candidate.confidence,
                box: observation.boundingBox
            )
        }
        allObservations.append(contentsOf: observations)
        let ordered = observations.sorted { left, right in
            if abs(left.box.midY - right.box.midY) > 0.02 {
                return left.box.midY > right.box.midY
            }
            return left.box.minX < right.box.minX
        }
        var lines: [[OrderedObservation]] = []
        for observation in ordered {
            if let last = lines.last,
               let first = last.first,
               abs(first.box.midY - observation.box.midY) <= 0.025 {
                lines[lines.count - 1].append(observation)
            } else {
                lines.append([observation])
            }
        }
        for line in lines {
            let value = line.sorted { $0.box.minX < $1.box.minX }
                .map(\.text)
                .joined(separator: " ")
            if pageLines.last != value {
                pageLines.append(value)
            }
        }
    }
    let text = pageLines.joined(separator: "\n")
    let confidence = allObservations.isEmpty
        ? 0.0
        : allObservations.reduce(0.0) { $0 + Double($1.confidence) } / Double(allObservations.count)

    _ = requestRevision
    return OCRPage(
        page_number: pageNumber,
        text: text,
        observation_count: allObservations.count,
        mean_confidence: confidence,
        line_break_count: max(0, pageLines.count - 1)
    )
}

private func nativePage(_ page: PDFPage, pageNumber: Int) -> OCRPage {
    let text = page.string ?? ""
    return OCRPage(
        page_number: pageNumber,
        text: text,
        observation_count: 0,
        mean_confidence: text.isEmpty ? 0.0 : 1.0,
        line_break_count: text.reduce(0) { $1 == "\n" ? $0 + 1 : $0 }
    )
}

private func run() throws -> OCRResponse {
    let (pdfURL, pagesArgument, mode) = try parseArguments()
    guard let document = PDFDocument(url: pdfURL) else {
        throw OCRFailure.unreadablePDF
    }

    let requestedPages: [Int]
    if pagesArgument == "all" {
        requestedPages = Array(1...document.pageCount)
    } else {
        let parsed = try pagesArgument.split(separator: ",").map { component -> Int in
            guard let page = Int(component), page > 0 else {
                throw OCRFailure.invalidPage("invalid one-based page number \(component)")
            }
            return page
        }
        requestedPages = Array(Set(parsed)).sorted()
    }
    guard !requestedPages.isEmpty else {
        throw OCRFailure.invalidPage("at least one page is required")
    }

    var pages: [OCRPage] = []
    let requestRevision = VNRecognizeTextRequest().revision
    for pageNumber in requestedPages {
        guard let page = document.page(at: pageNumber - 1) else {
            throw OCRFailure.missingPage(pageNumber)
        }
        if mode == "native" {
            pages.append(nativePage(page, pageNumber: pageNumber))
        } else {
            pages.append(try recognizePage(page, pageNumber: pageNumber, requestRevision: requestRevision))
        }
    }

    let runtime = RuntimeMetadata(
        helper_version: helperVersion,
        os_version: ProcessInfo.processInfo.operatingSystemVersionString,
        swift_language_version: "Swift 5+"
    )
    let recognizer = RecognizerMetadata(
        framework: mode == "native" ? "PDFKit" : "Vision",
        request: mode == "native" ? "PDFPage.string" : "VNRecognizeTextRequest",
        recognition_languages: mode == "native" ? [] : ["uk-UA"],
        recognition_level: mode == "native" ? "native" : "accurate",
        uses_cpu_only: true,
        revision: mode == "native" ? 0 : requestRevision
    )
    return OCRResponse(
        schema_version: schemaVersion,
        metadata: OCRMetadata(runtime: runtime, recognizer: recognizer),
        pages: pages
    )
}

do {
    let encoder = JSONEncoder()
    encoder.outputFormatting = [.sortedKeys]
    let data = try encoder.encode(run())
    FileHandle.standardOutput.write(data)
    FileHandle.standardOutput.write(Data([0x0A]))
} catch {
    fputs("apple_vision_ocr.swift: \(error.localizedDescription)\n", stderr)
    exit(1)
}
