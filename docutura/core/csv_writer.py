"""
CSV output engine for DocTura Desktop.

Supports per-sheet and combined CSV export.
"""

import csv
from pathlib import Path
from typing import List

from docutura.core.models import ExtractedTable


class CSVWriter:
    """Writes extracted tables to CSV files."""

    def __init__(self):
        pass

    def write_tables_to_csv(
        self,
        output_dir: Path,
        tables: List[ExtractedTable],
        combined: bool = False,
        base_name: str = "export",
    ) -> List[Path]:
        """
        Write tables to CSV files.

        Args:
            output_dir: Output directory
            tables: Tables to write
            combined: If True, write all tables to a single CSV
            base_name: Base name for output files

        Returns:
            List of created file paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        created_files = []

        if combined:
            # Write all tables to a single CSV file
            output_path = output_dir / f"{base_name}_combined.csv"
            self._write_combined_csv(output_path, tables)
            created_files.append(output_path)
        else:
            # Write each table to a separate CSV file
            for idx, table in enumerate(tables, start=1):
                filename = f"{base_name}_table_{idx}.csv"
                output_path = output_dir / filename
                self._write_single_table_csv(output_path, table)
                created_files.append(output_path)

        return created_files

    def _write_single_table_csv(self, output_path: Path, table: ExtractedTable) -> None:
        """Write a single table to CSV."""
        with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)

            for row in table.data:
                writer.writerow(row)

    def _write_combined_csv(
        self, output_path: Path, tables: List[ExtractedTable]
    ) -> None:
        """Write all tables to a single CSV file."""
        with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)

            for table_idx, table in enumerate(tables):
                # Add separator comment between tables
                if table_idx > 0:
                    writer.writerow([])  # Blank row
                    writer.writerow([f"--- Table {table_idx + 1} ---"])

                # Add section title if available
                if table.section_title:
                    writer.writerow([f"Section: {table.section_title}"])

                # Write table data
                for row in table.data:
                    writer.writerow(row)
