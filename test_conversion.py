"""
Quick test script to verify DocTura conversion works.

Usage: python test_conversion.py <path_to_pdf>
"""

import sys
from pathlib import Path

from docutura.app.main import get_default_paths, initialize_plugins
from docutura.core.controller import ConversionController
from docutura.core.models import ExtractionOptions, OutputFormat

def test_conversion(pdf_path: str):
    """Test conversion of a single PDF file."""

    input_file = Path(pdf_path)

    if not input_file.exists():
        print(f"ERROR: File not found: {pdf_path}")
        return

    print(f"Testing conversion of: {input_file.name}")
    print("=" * 60)

    # Initialize
    plugin_registry = initialize_plugins()
    output_dir, audit_dir = get_default_paths()

    controller = ConversionController(
        plugin_registry=plugin_registry,
        output_dir=output_dir,
        audit_dir=audit_dir
    )

    # Configure options
    options = ExtractionOptions(
        output_formats=[OutputFormat.XLSX],  # Just Excel for now
        theme="corporate",
    )

    # Convert
    print("Converting...")
    result = controller.convert_document(input_file, options)

    # Show results
    print("\n" + "=" * 60)
    if result.success:
        print("✓ SUCCESS!")
        print(f"\nPlugin: {result.metadata.plugin_id or 'Generic'}")
        print(f"Validation: {result.validation_report.overall_status.value.upper()}")
        print(f"Processing time: {result.processing_time_seconds:.2f}s")
        print(f"\nOutput files ({len(result.output_files)}):")
        for f in result.output_files:
            print(f"  - {f}")

        if result.validation_report.issues:
            print(f"\nValidation issues ({len(result.validation_report.issues)}):")
            for issue in result.validation_report.issues[:5]:  # First 5
                print(f"  - {issue.severity.value}: {issue.message}")
    else:
        print("✗ FAILED!")
        print(f"Error: {result.error_message}")

    print("=" * 60)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_conversion.py <path_to_pdf>")
        print("\nExample:")
        print("  python test_conversion.py Working_Documents\\Computer_Studies_TASS_And_CASS_Statistics.pdf")
    else:
        test_conversion(sys.argv[1])
