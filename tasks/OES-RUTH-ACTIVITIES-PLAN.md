# Issue: Implement & Support Specialized Activities for OES & RUTH Tracks

## Context
The **OES (Old East Slavic)** and **RUTH (Ruthenian)** tracks are designed as "Linguistic Archaeology" seminars. Unlike core language modules (A1-B2) which focus on drills, these tracks require students to analyze primary sources, trace sound changes, and understand paleography.

Current status:
- Backend schemas and MDX generator updated for `etymology-trace`, `transcription`, and `grammar-identify`.
- Frontend (React) exists for `etymology-trace` and `grammar-identify`.
- **CRITICAL GAP**: `transcription` has no UI component.
- **EXPANSION NEEDED**: Paleography, Dialect Comparison, and Translation Critique are missing both backend and frontend.

---

## 1. Transcription (Immediate Priority)
**Task**: User transcribes archaic script into modern Cyrillic.

### Backend Requirements
- **Type**: `transcription`
- **Fields**:
  - `original`: Archaic text/image link
  - `answer`: Modern Cyrillic equivalent
  - `instruction`: (Optional) Context about the script (e.g., Glagolitic)

### UI/UX Design
- **Display**: The `original` text displayed in a large, "archaic" CSS font (e.g., a custom Uncial font) or an image.
- **Input**: A text field for the user to type the transcription.
- **Feature**: A **Virtual Keyboard** strip above the input containing historical letters (`ѣ`, `ѫ`, `ѧ`, `ѯ`, etc.) that are difficult to type on modern keyboards.
- **Validation**: Strict character matching, but ignoring case or titlo marks if specified.

---

## 2. Paleography Analysis (Planned)
**Task**: Identifying visual features of manuscripts.

### Backend Requirements
- **Type**: `paleography-analysis`
- **Fields**:
  - `image_url`: Link to high-res manuscript scan
  - `hotspots`: Array of `{ x, y, label, explanation }`
  - `options`: List of terms (Ustav, Skoropys, Titlo, Ligature)

### UI/UX Design
- **Display**: High-quality image viewer with zoom capabilities.
- **Interaction**: Circular "hotspots" on the image. When clicked, a modal or tooltip asks "What feature is this?"
- **Feedback**: After selecting, show an explanation of how that feature dates the manuscript or identifies the scribe.

---

## 3. Dialect Comparison (Planned)
**Task**: Side-by-side contrast of regional features.

### Backend Requirements
- **Type**: `dialect-comparison`
- **Fields**:
  - `text_a`: (e.g., Kyiv source)
  - `text_b`: (e.g., Novgorod source)
  - `features`: Array of `{ feature_name, value_a, value_b, explanation }`

### UI/UX Design
- **Display**: Split-screen view showing two text blocks.
- **Interaction**: "Highlight & Link". User clicks a word in Text A and its equivalent in Text B.
- **Feedback**: A "Result Table" appears showing the divergence (e.g., "Kyiv uses -ові [Southern], Novgorod uses -у [Northern]").

---

## 4. Translation Critique (Planned)
**Task**: Evaluating modern interpretations of archaic texts.

### Backend Requirements
- **Type**: `translation-critique`
- **Fields**:
  - `original`: OES/RUTH text
  - `translations`: Array of `{ translator, text, accuracy_score, notes }`
  - `focus_points`: Key words that are often mistranslated

### UI/UX Design
- **Display**: Original text at the top. Multiple modern translations in cards below.
- **Interaction**: "Critique Mode". User clicks on words in the translations that they think are problematic based on the lesson's grammar.
- **Feedback**: Reveal "Expert Verdict" for each translation, explaining the nuance (e.g., "This translation uses Russian-style aspect which didn't exist yet").

---

## Implementation Roadmap

### Phase 1: Frontend Fixes
1. Create `docusaurus/src/components/Transcription.tsx`.
2. Add "Historical Character Picker" utility.

### Phase 2: Schema Expansion
1. Update `schemas/activities-base.schema.json` with `paleography-analysis`, `dialect-comparison`, and `translation-critique`.
2. Update `scripts/yaml_activities.py` dataclasses and MDX methods.

### Phase 3: Advanced UI
1. Implement `PaleographyAnalysis.tsx` using a simple hotspot library.
2. Implement `DialectComparison.tsx` with side-by-side highlighting.

### Phase 4: Track Deployment
1. Roll out OES Modules 2-10 using these new interactive types.
