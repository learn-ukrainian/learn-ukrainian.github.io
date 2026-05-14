// Apple Vision OCR (VNRecognizeTextRequest) for ESUM feasibility test.
// Usage: swift apple_vision_ocr.swift <png_path>
// Reads recognized lines top-to-bottom, left-to-right, prints to stdout.

import Foundation
import Vision
import AppKit

guard CommandLine.arguments.count >= 2 else {
    FileHandle.standardError.write("usage: apple_vision_ocr.swift <png>\n".data(using: .utf8)!)
    exit(2)
}
let path = CommandLine.arguments[1]
guard let nsImage = NSImage(contentsOfFile: path),
      let tiff = nsImage.tiffRepresentation,
      let rep = NSBitmapImageRep(data: tiff),
      let cgImage = rep.cgImage else {
    FileHandle.standardError.write("cannot load image: \(path)\n".data(using: .utf8)!)
    exit(3)
}

let request = VNRecognizeTextRequest { (req, err) in
    if let err = err {
        FileHandle.standardError.write("vision error: \(err)\n".data(using: .utf8)!)
        exit(4)
    }
    guard let observations = req.results as? [VNRecognizedTextObservation] else { return }

    // Sort observations by reading order: top→bottom, then left→right within bands.
    // Vision returns boundingBox in normalized coords with origin at bottom-left.
    let sorted = observations.sorted { a, b in
        let aY = 1.0 - a.boundingBox.midY  // flip to top-origin
        let bY = 1.0 - b.boundingBox.midY
        let bandHeight: CGFloat = 0.012
        if abs(aY - bY) < bandHeight {
            return a.boundingBox.midX < b.boundingBox.midX
        }
        return aY < bY
    }

    for obs in sorted {
        if let candidate = obs.topCandidates(1).first {
            print(candidate.string)
        }
    }
}
request.recognitionLevel = .accurate
request.usesLanguageCorrection = true
request.recognitionLanguages = ["uk-UA", "ru-RU", "pl-PL", "cs-CZ", "sk-SK", "bg-BG", "sr-Cyrl", "de-DE", "en-US"]

let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
do {
    try handler.perform([request])
} catch {
    FileHandle.standardError.write("perform error: \(error)\n".data(using: .utf8)!)
    exit(5)
}
