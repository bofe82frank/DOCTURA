# DocTura Desktop

**Generic, offline-first, plugin-driven document intelligence application**

DocTura Desktop converts semi-structured and structured documents into high-quality Excel, CSV, Word, and PDF outputs, with deterministic validation, audit logging, and optional AI summarisation.

## Key Features

- **Hybrid Extraction**: Page-preserved sheets + logical table reconstruction
- **Smart Segmentation**: Score-domain & header-repetition strategies
- **Multiple Output Formats**: XLSX, CSV, DOCX, PDF
- **Reverse Conversion**: Excel/Word → PDF
- **Deterministic Validation**: Mandatory quality checks
- **Plugin Architecture**: Extensible system with built-in WAEC and staff roster plugins
- **Dual Themes**: Corporate (navy/gold) & Indigenous (earth tones)
- **Audit Logging**: Enterprise-grade tracking
- **Offline-First**: Core functionality works without internet

## Design Principles

The system design is informed by the TASS Scaled Essay truncation incident:

1. **Page boundaries are unreliable**
2. **Visual continuity ≠ logical continuity**
3. **Domain rules must override layout**
4. **Extraction, routing, and layout must be decoupled**

## Installation

```bash
# Clone the repository
git clone https://github.com/bofe82frank/DOCTURA.git
cd DOCTURA

# Install in development mode
pip install -e .

# Optional: Install with AI support
pip install -e ".[ai]"

# Optional: Install development tools
pip install -e ".[dev]"
```

## Quick Start

```bash
# Run the application
python -m docutura.app.main

# Or use the installed command
docutura
```

## Supported Inputs

- PDF (native and scanned)
- DOCX
- Images (PNG, JPG, TIFF)
- Audio (WAV, MP3, M4A)

## Output Options

### Excel
- Page-preserved worksheets (Page_01, Page_02, ...)
- Logical tables (reconstructed across page boundaries)
- Single or multi-worksheet layouts
- Vertical stacking or horizontal placement

### Word
- Portrait or landscape orientation
- Optional page breaks per table
- Section titles as headings
- Clean table formatting

### PDF
- Reverse conversion from Excel/Word
- Structural rendering (deterministic)
- Preserves orientation and layout

### CSV
- Per-sheet or combined export

## Architecture

```
docutura/
├── app/           # GUI application (PySide6)
├── core/          # Extraction, validation, output engines
├── plugins/       # Plugin system and built-in plugins
├── enterprise/    # Audit logging and policy enforcement
└── tests/         # Comprehensive test suite
```

## Built-in Plugins

### 1. WAEC Marks Distribution Plugin
- Score-domain routing (prevents truncation)
- Paper splits detection
- Distribution validation

### 2. International Staff List Plugin
- Header-based segmentation
- Section grouping
- Roster validation

## Themes

### Corporate Theme
- Professional, neutral color scheme
- Navy blue primary, gold accents
- For enterprise and government use

### Indigenous Theme
- African-inspired earth tones
- Forest green, burnt orange accents
- Culturally grounded and warm

## Validation

All outputs undergo deterministic validation:
- Percent totals = 100.00 ± tolerance
- No duplicate rows
- Score ranges enforced
- Monotonic cumulative frequency
- Header consistency checks
- No orphan rows

## License

MIT License

## Support

For issues and feedback: https://github.com/bofe82frank/DOCTURA/issues
