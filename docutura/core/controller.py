"""
Main conversion controller for DocTura Desktop.

Orchestrates the complete document conversion pipeline.
"""

import hashlib
import time
from pathlib import Path
from typing import List, Optional, Tuple

from docutura.core.csv_writer import CSVWriter
from docutura.core.excel_writer import ExcelWriter
from docutura.core.extractor import DocumentExtractor
from docutura.core.models import (
    ConversionResult,
    DocumentMetadata,
    ExtractionMode,
    ExtractionOptions,
    OutputFormat,
    RoutedTables,
    ValidationReport,
    ValidationStatus,
)
from docutura.core.naming import SmartNamingEngine
from docutura.core.segmentation import TableSegmenter
from docutura.core.themes import THEMES, ThemeType, get_theme
from docutura.core.validator import TableValidator
from docutura.core.word_writer import WordWriter
from docutura.enterprise.audit import AuditLogger
from docutura.plugins.base import DocumentPlugin, PluginRegistry


class ConversionController:
    """Main controller for document conversion."""

    def __init__(
        self,
        plugin_registry: PluginRegistry,
        output_dir: Path,
        audit_dir: Optional[Path] = None,
    ):
        """
        Initialize conversion controller.

        Args:
            plugin_registry: Registry of document plugins
            output_dir: Output directory for converted files
            audit_dir: Directory for audit logs (optional)
        """
        self.plugin_registry = plugin_registry
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize audit logger if directory provided
        self.audit_logger = AuditLogger(audit_dir) if audit_dir else None

        # Initialize naming engine
        self.naming_engine = SmartNamingEngine()

    def convert_document(
        self, input_file: Path, options: ExtractionOptions
    ) -> ConversionResult:
        """
        Convert a document.

        Args:
            input_file: Path to input file
            options: Extraction and output options

        Returns:
            Conversion result
        """
        start_time = time.time()

        try:
            # Step 1: Extract content
            extractor = DocumentExtractor(
                enable_ocr=options.enable_ocr, ocr_language=options.ocr_language
            )

            tables_data, page_texts, context = extractor.extract(input_file)

            # Step 2: Detect plugin
            plugin_result = self.plugin_registry.detect_plugin(
                tables_data, page_texts, context
            )

            if plugin_result:
                plugin, detection = plugin_result
                print(
                    f"Detected plugin: {plugin.get_plugin_id()} "
                    f"(confidence: {detection.confidence:.2%})"
                )
            else:
                plugin = None
                print("No plugin detected, using generic processing")

            # Step 3: Create page-preserved tables
            page_tables = extractor.create_page_preserved_tables(tables_data)

            # Step 4: Segment logical tables
            segmenter = TableSegmenter()

            if plugin:
                strategy = plugin.get_segmentation_strategy()
                score_domains = plugin.get_score_domains()
            else:
                strategy = segmenter._detect_strategy(tables_data)
                score_domains = None

            logical_tables = segmenter.segment_tables(
                tables_data, strategy, score_domains=score_domains
            )

            # Step 5: Extract metadata
            if plugin:
                metadata = plugin.extract_metadata(tables_data, page_texts, context)
                metadata.plugin_confidence = detection.confidence
            else:
                metadata = DocumentMetadata()

            # Complete metadata
            metadata.input_file_path = str(input_file)
            metadata.input_file_hash = self._compute_file_hash(input_file)
            metadata.extraction_mode = options.mode.value
            metadata.excel_layout_mode = options.excel_layout.value
            metadata.word_orientation = options.word_orientation.value
            metadata.output_formats = [fmt.value for fmt in options.output_formats]
            metadata.theme = options.theme

            # Step 6: Validate tables
            validator = TableValidator(tolerance=options.validation_tolerance)

            # Get tables based on extraction mode
            routed = RoutedTables(page_tables=page_tables, logical_tables=logical_tables)
            tables_to_validate = routed.get_all_tables(options.mode)

            if options.validation_enabled:
                validation_report = validator.validate_tables(tables_to_validate)
            else:
                validation_report = ValidationReport(
                    overall_status=ValidationStatus.PASSED,
                    issues=[],
                    tables_validated=0,
                    tables_passed=0,
                    tables_with_warnings=0,
                    tables_failed=0,
                )

            # Update metadata with validation info
            metadata.validation_status = validation_report.overall_status.value
            metadata.validation_issues_count = len(validation_report.issues)

            # Step 7: Generate outputs
            output_files = []
            theme = get_theme(ThemeType(options.theme))

            # Create output subdirectory
            output_subdir = self.output_dir / self.naming_engine.generate_directory_name(
                input_file, metadata
            )
            output_subdir.mkdir(parents=True, exist_ok=True)

            for output_format in options.output_formats:
                if output_format == OutputFormat.XLSX:
                    output_path = self._generate_excel_output(
                        output_subdir,
                        input_file,
                        page_tables,
                        logical_tables,
                        metadata,
                        validation_report,
                        options,
                        theme,
                    )
                    output_files.append(output_path)

                elif output_format == OutputFormat.DOCX:
                    output_path = self._generate_word_output(
                        output_subdir,
                        input_file,
                        logical_tables,
                        metadata,
                        options,
                        theme,
                    )
                    output_files.append(output_path)

                elif output_format == OutputFormat.CSV:
                    csv_files = self._generate_csv_output(
                        output_subdir, input_file, logical_tables, metadata, options
                    )
                    output_files.extend(csv_files)

            # Step 8: Create result
            processing_time = time.time() - start_time

            result = ConversionResult(
                success=True,
                input_file=input_file,
                output_files=output_files,
                metadata=metadata,
                validation_report=validation_report,
                processing_time_seconds=processing_time,
            )

            # Step 9: Audit logging
            if self.audit_logger and options.audit_logging_enabled:
                self.audit_logger.log_conversion(result)

            return result

        except Exception as e:
            # Handle errors
            processing_time = time.time() - start_time

            return ConversionResult(
                success=False,
                input_file=input_file,
                output_files=[],
                metadata=DocumentMetadata(),
                validation_report=ValidationReport(
                    overall_status=ValidationStatus.FAILED,
                    issues=[],
                    tables_validated=0,
                    tables_passed=0,
                    tables_with_warnings=0,
                    tables_failed=0,
                ),
                error_message=str(e),
                processing_time_seconds=processing_time,
            )

    def _generate_excel_output(
        self, output_dir, input_file, page_tables, logical_tables, metadata, validation_report, options, theme
    ) -> Path:
        """Generate Excel output."""
        writer = ExcelWriter(
            layout_mode=options.excel_layout,
            add_borders=options.excel_add_borders,
            freeze_headers=options.excel_freeze_headers,
            theme=theme,
        )

        output_name = self.naming_engine.generate_output_name(
            input_file, metadata, OutputFormat.XLSX
        )
        output_path = output_dir / output_name

        writer.write_to_excel(
            output_path,
            page_tables,
            logical_tables,
            metadata if options.metadata_sheet_enabled else None,
            validation_report,
        )

        return output_path

    def _generate_word_output(
        self, output_dir, input_file, logical_tables, metadata, options, theme
    ) -> Path:
        """Generate Word output."""
        writer = WordWriter(
            orientation=options.word_orientation,
            page_break_per_table=options.word_page_break_per_table,
            include_images=options.word_include_images,
            theme=theme,
        )

        output_name = self.naming_engine.generate_output_name(
            input_file, metadata, OutputFormat.DOCX
        )
        output_path = output_dir / output_name

        writer.write_to_word(output_path, logical_tables, metadata)

        return output_path

    def _generate_csv_output(
        self, output_dir, input_file, logical_tables, metadata, options
    ) -> List[Path]:
        """Generate CSV output(s)."""
        writer = CSVWriter()

        base_name = self.naming_engine._sanitize(
            metadata.subject_or_code if metadata.subject_or_code else input_file.stem
        )

        return writer.write_tables_to_csv(
            output_dir, logical_tables, combined=False, base_name=base_name
        )

    @staticmethod
    def _compute_file_hash(file_path: Path) -> str:
        """Compute SHA-256 hash of file."""
        sha256 = hashlib.sha256()

        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)

        return sha256.hexdigest()
