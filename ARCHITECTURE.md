# DocTura Desktop - Architecture Overview

## System Design Principles

The DocTura architecture is **permanently informed** by the TASS Scaled Essay truncation incident, which established these invariants:

1. **Page boundaries are unreliable** - PDF page breaks don't respect logical table boundaries
2. **Visual continuity ≠ logical continuity** - What looks continuous may not be semantically related
3. **Domain rules must override layout** - Business logic (score ranges, headers) trumps visual presentation
4. **Extraction, routing, and layout must be decoupled** - Separation of concerns is mandatory

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     DocTura Desktop                          │
│                                                               │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐│
│  │  App Layer  │  │ Plugin Layer │  │ Enterprise Layer    ││
│  │  (PySide6)  │  │              │  │ (Audit & Policy)    ││
│  └──────┬──────┘  └──────┬───────┘  └──────────┬──────────┘│
│         │                │                      │            │
│         └────────────────┼──────────────────────┘            │
│                          │                                   │
│                  ┌───────▼────────┐                          │
│                  │   Core Engine  │                          │
│                  │                │                          │
│                  │ • Extractor    │                          │
│                  │ • Segmenter    │                          │
│                  │ • Validator    │                          │
│                  │ • Writers      │                          │
│                  └────────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Extraction Layer (`docutura/core/extractor.py`)

**Purpose**: Convert documents to structured data

**Key Features**:
- Multi-format support (PDF, DOCX, images)
- Native text extraction (pdfplumber, python-docx)
- OCR fallback (pytesseract)
- Quality detection (native vs scanned)

**Critical Behavior**: Never assume page boundaries define data boundaries

### 2. Segmentation Layer (`docutura/core/segmentation.py`)

**Purpose**: Reconstruct logical tables from page-split data

**Strategies**:

1. **Score-Domain Segmentation**
   - Used for: Statistical distributions (WAEC reports)
   - Prevents: Scaled Essay truncation
   - Method: Group rows by score range (0-19, 15-40, etc.)
   - Ignores: Page breaks entirely

2. **Header-Repetition Segmentation**
   - Used for: Rosters (staff lists, student records)
   - Prevents: Orphan rows and broken sections
   - Method: Detect repeated headers, segment by occurrence
   - Preserves: Section titles and groupings

**Output**: Two parallel representations:
- Page tables (Page_01, Page_02, ...) - for traceability
- Logical tables (reconstructed) - for data integrity

### 3. Validation Layer (`docutura/core/validator.py`)

**Purpose**: Deterministic quality assurance

**Generic Rules**:
- Percent columns sum to 100.00 ± tolerance
- No duplicate rows
- Score ranges obey domain constraints
- Monotonic cumulative frequency
- Non-negative counts

**Domain-Specific Rules**:
- Distribution tables: frequency/percent/cumulative coherence
- Roster tables: header-before-data, no orphan rows

**Critical**: Validation never modifies data, only reports issues

### 4. Output Layer (`docutura/core/`)

**Writers**:

1. **Excel Writer** (`excel_writer.py`)
   - Supports 3 layout modes:
     - Separate sheets per table
     - Single sheet vertical stacking
     - Single sheet horizontal placement
   - Generates Document_Metadata sheet
   - Applies theme styling to headers

2. **Word Writer** (`word_writer.py`)
   - Portrait/Landscape orientation
   - Optional page breaks per table
   - Section titles as headings
   - Theme-aware styling

3. **CSV Writer** (`csv_writer.py`)
   - Per-table or combined export
   - Simple, deterministic output

**Critical**: Output format never affects data integrity

### 5. Plugin System (`docutura/plugins/`)

**Base Interface** (`base.py`):
- `detect()` - Confidence-based document classification
- `extract_metadata()` - Document-specific metadata
- `get_segmentation_strategy()` - Strategy selection
- `get_score_domains()` - Domain definitions
- `post_process_tables()` - Optional cleanup
- `summarize()` - Optional AI-safe summary

**Built-in Plugins**:

1. **WAEC Marks Distribution** (`waec_marksdist.py`)
   - Detects: TASS/CASS keywords, distribution structure
   - Strategy: Score-domain segmentation
   - Domains: Scaled Objective (0-19), Scaled Essay (15-40)
   - Prevents: The TASS incident

2. **International Staff List** (`staff_list.py`)
   - Detects: Roster keywords, repeated headers
   - Strategy: Header-repetition segmentation
   - Preserves: Section groupings

### 6. Theme System (`docutura/core/themes.py`)

**Corporate Theme**:
- Navy blue (#0B1F3B) + Gold (#C9A227)
- For: Enterprise, government, academic
- Tone: Formal, authoritative

**Indigenous Theme**:
- Earth brown (#5A3E2B) + Burnt orange (#C05621)
- For: African identity, cultural authenticity
- Tone: Grounded, warm

**Application**: Entire UI, export styling (never data)

### 7. Enterprise Layer (`docutura/enterprise/`)

**Audit Logger** (`audit.py`):
- Records every conversion with:
  - Input/output file hashes (SHA-256)
  - Plugin ID, version, confidence
  - Extraction configuration
  - Validation results
  - Performance metrics
- Outputs: JSON logs + JSONL index
- Use case: Compliance, reproducibility

## Data Flow

```
Input File
    │
    ▼
[Extractor] ──────► tables_data (raw)
    │                page_texts
    │                context
    ▼
[Plugin Detection] ─► plugin, confidence, metadata
    │
    ▼
[Segmentation] ─────► page_tables (Page_01, ...)
    │                 logical_tables (reconstructed)
    ▼
[Validation] ───────► validation_report
    │
    ▼
[Output Writers] ───► XLSX, DOCX, CSV, PDF
    │
    ▼
[Audit Logger] ─────► audit.json
```

## Key Design Decisions

### 1. Hybrid Extraction (Default)

**Why**: Balances traceability with data integrity
- Page tables: debugging, audits
- Logical tables: actual data use

**Alternative rejected**: Logical-only (loses traceability)

### 2. Deterministic Validation

**Why**: AI cannot reliably validate numerical constraints
- Percent totals MUST be 100.00
- Frequencies MUST be non-negative
- Cumulative MUST be monotonic

**Alternative rejected**: AI-based validation (unreliable)

### 3. Plugin Architecture

**Why**: Generic system, domain-specific intelligence
- Core: Handles all documents generically
- Plugins: Add domain knowledge (WAEC, rosters)

**Extensibility**: New plugins drop into `docutura/plugins/`

### 4. Offline-First

**Why**: Core must work without internet
- Extraction: Local libraries only
- Validation: Deterministic rules
- AI: Optional, safe summarization only

**AI limitations**:
- NO data modification
- NO recomputation
- NO inference of missing values

## Testing Strategy

### Unit Tests (`docutura/tests/`)
- Theme system
- Data models
- Validation logic
- Naming engine
- Plugin detection

### Integration Tests (Future)
- End-to-end conversion
- Plugin workflows
- Output format verification

### Test Data
- Located in `Working_Documents/` (git-ignored)
- Includes real WAEC and staff list PDFs

## Configuration

**Defaults** (hardcoded for v0.1):
- Extraction Mode: HYBRID
- Excel Layout: SEPARATE_SHEETS
- Word Orientation: PORTRAIT
- Theme: CORPORATE
- Validation: ENABLED
- Audit Logging: ENABLED

**Future**: Settings UI for user customization

## Extension Points

1. **New Plugins**
   - Inherit from `DocumentPlugin`
   - Implement detection logic
   - Register in `app/main.py`

2. **New Output Formats**
   - Create writer in `core/`
   - Add to `OutputFormat` enum
   - Integrate in `controller.py`

3. **New Validation Rules**
   - Add to `TableValidator`
   - Plugin-specific: override `get_validation_rules()`

4. **New Themes**
   - Define in `themes.py`
   - Add to `ThemeType` enum
   - No code changes needed

## Performance Considerations

- **Streaming**: Not implemented (v0.1 loads full documents)
- **Parallelization**: Sequential processing (future: batch mode)
- **Caching**: None (future: plugin detection caching)
- **Memory**: PDFs loaded into memory (suitable for typical reports <100 pages)

## Security

- **File handling**: Sandboxed to output directories
- **OCR**: Local (pytesseract), no cloud APIs
- **Audit logs**: Local filesystem only
- **No telemetry**: Fully offline

## Known Limitations

1. **OCR table extraction**: Basic text only, no table structure
2. **Image-based tables**: Require manual definition (future: ML models)
3. **Multi-column PDFs**: May confuse table detection
4. **Password-protected PDFs**: Not supported

## Future Enhancements

1. **Reverse PDF Generation**: Excel/Word → PDF (structural rendering)
2. **AI Summarization**: Optional Claude/GPT integration (safe mode)
3. **Audio Transcription**: Whisper integration for WAV/MP3
4. **CLI Mode**: Headless operation
5. **Batch Processing**: Queue multiple files
6. **Settings UI**: User-configurable defaults
7. **Plugin Marketplace**: Community plugins

---

**Version**: 0.1.0
**Last Updated**: 2026-01-04
