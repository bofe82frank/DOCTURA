"""
Core data models for DocTura Desktop.

Defines extraction options, table structures, validation reports, and metadata.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


class ExtractionMode(str, Enum):
    """Extraction mode options."""

    HYBRID = "hybrid"  # Page-preserved + logical tables (DEFAULT)
    PAGE_ONLY = "page_only"  # Only page-preserved sheets
    LOGICAL_ONLY = "logical_only"  # Only logical tables


class ExcelLayoutMode(str, Enum):
    """Excel worksheet layout options."""

    SEPARATE_SHEETS = "separate_sheets"  # Each table → separate worksheet
    SINGLE_SHEET_VERTICAL = "single_sheet_vertical"  # All tables → single sheet, stacked down
    SINGLE_SHEET_HORIZONTAL = "single_sheet_horizontal"  # All tables → single sheet, across


class WordOrientation(str, Enum):
    """Word document page orientation."""

    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"


class SegmentationStrategy(str, Enum):
    """Table segmentation strategies."""

    SCORE_DOMAIN = "score_domain"  # Based on score ranges (e.g., 0-19, 15-40)
    HEADER_REPETITION = "header_repetition"  # Based on repeated headers
    AUTO = "auto"  # Plugin decides


class OutputFormat(str, Enum):
    """Supported output formats."""

    XLSX = "xlsx"
    CSV = "csv"
    DOCX = "docx"
    PDF = "pdf"


class ValidationStatus(str, Enum):
    """Validation result status."""

    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"


@dataclass
class ScoreDomain:
    """Score domain definition for statistical distributions."""

    name: str  # e.g., "Scaled Objective", "Scaled Essay"
    min_score: int
    max_score: int
    description: str = ""


@dataclass
class TableSchema:
    """Schema definition for extracted tables."""

    headers: List[str]
    column_count: int
    has_header: bool = True
    header_row_indices: List[int] = field(default_factory=list)


@dataclass
class ExtractedTable:
    """Represents an extracted table (page-preserved or logical)."""

    data: List[List[Any]]  # Raw table data
    schema: TableSchema
    source_pages: List[int]  # Pages this table was extracted from (1-indexed)
    table_type: str  # "page_preserved" or "logical"
    segmentation_strategy: Optional[SegmentationStrategy] = None
    section_title: Optional[str] = None  # For rosters with section grouping
    score_domain: Optional[ScoreDomain] = None  # For score-domain segmented tables

    @property
    def row_count(self) -> int:
        """Number of rows in the table."""
        return len(self.data)

    @property
    def is_empty(self) -> bool:
        """Check if table is empty."""
        return len(self.data) == 0


@dataclass
class RoutedTables:
    """Container for both page-preserved and logical tables."""

    page_tables: List[ExtractedTable]  # One per page
    logical_tables: List[ExtractedTable]  # Reconstructed logical tables

    def get_all_tables(self, mode: ExtractionMode) -> List[ExtractedTable]:
        """Get tables based on extraction mode."""
        if mode == ExtractionMode.HYBRID:
            return self.page_tables + self.logical_tables
        elif mode == ExtractionMode.PAGE_ONLY:
            return self.page_tables
        elif mode == ExtractionMode.LOGICAL_ONLY:
            return self.logical_tables
        return []


class ExtractionOptions(BaseModel):
    """User-configurable extraction and output options."""

    # Extraction settings
    mode: ExtractionMode = ExtractionMode.HYBRID
    enable_ocr: bool = False
    ocr_language: str = "eng"

    # Output formats
    output_formats: List[OutputFormat] = Field(default_factory=lambda: [OutputFormat.XLSX])

    # Excel layout options
    excel_layout: ExcelLayoutMode = ExcelLayoutMode.SEPARATE_SHEETS
    excel_add_borders: bool = True
    excel_freeze_headers: bool = True

    # Word layout options
    word_orientation: WordOrientation = WordOrientation.PORTRAIT
    word_page_break_per_table: bool = False
    word_include_images: bool = True

    # PDF export (reverse conversion)
    pdf_fit_to_width: bool = True
    pdf_include_gridlines: bool = False

    # Metadata
    metadata_sheet_enabled: bool = True
    metadata_policy: str = "sheet_only"  # "sheet_only" or "duplicate"

    # Validation
    validation_enabled: bool = True
    validation_tolerance: float = 0.01  # For percent totals

    # AI summarization (optional)
    ai_summary_enabled: bool = False
    ai_provider: Optional[str] = None  # "anthropic" or "openai"

    # Theme
    theme: str = "corporate"  # "corporate" or "indigenous"

    # Audit logging
    audit_logging_enabled: bool = True

    class Config:
        use_enum_values = True


@dataclass
class ValidationIssue:
    """A single validation issue."""

    severity: ValidationStatus
    message: str
    table_name: str
    row_index: Optional[int] = None
    column_name: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationReport:
    """Complete validation report for a document."""

    overall_status: ValidationStatus
    issues: List[ValidationIssue]
    tables_validated: int
    tables_passed: int
    tables_with_warnings: int
    tables_failed: int
    timestamp: datetime = field(default_factory=datetime.now)

    def add_issue(self, issue: ValidationIssue) -> None:
        """Add a validation issue."""
        self.issues.append(issue)

        # Update overall status
        if issue.severity == ValidationStatus.FAILED:
            self.overall_status = ValidationStatus.FAILED
        elif issue.severity == ValidationStatus.WARNING and self.overall_status != ValidationStatus.FAILED:
            self.overall_status = ValidationStatus.WARNING

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "overall_status": self.overall_status.value,
            "issues": [
                {
                    "severity": issue.severity.value,
                    "message": issue.message,
                    "table_name": issue.table_name,
                    "row_index": issue.row_index,
                    "column_name": issue.column_name,
                    "details": issue.details,
                }
                for issue in self.issues
            ],
            "summary": {
                "tables_validated": self.tables_validated,
                "tables_passed": self.tables_passed,
                "tables_with_warnings": self.tables_with_warnings,
                "tables_failed": self.tables_failed,
            },
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class DocumentMetadata:
    """Metadata extracted from document."""

    # Document identification
    title: Optional[str] = None
    organization: Optional[str] = None
    reporting_period: Optional[str] = None
    subject_or_code: Optional[str] = None

    # Processing metadata
    plugin_id: Optional[str] = None
    plugin_version: Optional[str] = None
    plugin_confidence: float = 0.0
    extraction_mode: str = "hybrid"
    excel_layout_mode: Optional[str] = None
    word_orientation: Optional[str] = None
    output_formats: List[str] = field(default_factory=list)
    theme: str = "corporate"

    # File information
    input_file_path: str = ""
    input_file_hash: str = ""  # SHA-256
    timestamp: datetime = field(default_factory=datetime.now)

    # Validation
    validation_status: Optional[str] = None
    validation_issues_count: int = 0

    def to_worksheet_data(self) -> List[Tuple[str, Any]]:
        """Convert to list of (key, value) pairs for Excel sheet."""
        return [
            ("Document Title", self.title or "N/A"),
            ("Organization", self.organization or "N/A"),
            ("Reporting Period", self.reporting_period or "N/A"),
            ("Subject/Code", self.subject_or_code or "N/A"),
            ("", ""),  # Blank row
            ("Plugin ID", self.plugin_id or "N/A"),
            ("Plugin Version", self.plugin_version or "N/A"),
            ("Plugin Confidence", f"{self.plugin_confidence:.2%}"),
            ("", ""),  # Blank row
            ("Extraction Mode", self.extraction_mode),
            ("Excel Layout", self.excel_layout_mode or "N/A"),
            ("Word Orientation", self.word_orientation or "N/A"),
            ("Output Formats", ", ".join(self.output_formats)),
            ("Theme", self.theme.capitalize()),
            ("", ""),  # Blank row
            ("Input File", Path(self.input_file_path).name),
            ("File Hash (SHA-256)", self.input_file_hash),
            ("Processed At", self.timestamp.strftime("%Y-%m-%d %H:%M:%S")),
            ("", ""),  # Blank row
            ("Validation Status", self.validation_status or "N/A"),
            ("Validation Issues", self.validation_issues_count),
        ]


@dataclass
class ConversionResult:
    """Result of a document conversion operation."""

    success: bool
    input_file: Path
    output_files: List[Path]
    metadata: DocumentMetadata
    validation_report: ValidationReport
    error_message: Optional[str] = None
    processing_time_seconds: float = 0.0

    def get_summary(self) -> str:
        """Get human-readable summary."""
        if not self.success:
            return f"Failed: {self.error_message}"

        formats = ", ".join([f.suffix.upper()[1:] for f in self.output_files])
        return f"Success: Generated {len(self.output_files)} file(s) ({formats}) in {self.processing_time_seconds:.2f}s"
