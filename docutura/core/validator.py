"""
Deterministic validation system for DocTura Desktop.

Validates extracted tables using generic and domain-specific rules.
"""

from typing import List, Optional

from docutura.core.models import (
    ExtractedTable,
    ValidationIssue,
    ValidationReport,
    ValidationStatus,
)


class TableValidator:
    """Validates extracted tables using deterministic rules."""

    def __init__(self, tolerance: float = 0.01):
        """
        Initialize validator.

        Args:
            tolerance: Tolerance for percent total validation (default 0.01 = 1%)
        """
        self.tolerance = tolerance

    def validate_tables(
        self, tables: List[ExtractedTable], table_names: Optional[List[str]] = None
    ) -> ValidationReport:
        """
        Validate all tables.

        Args:
            tables: List of tables to validate
            table_names: Optional names for tables (for error reporting)

        Returns:
            ValidationReport with all issues
        """
        report = ValidationReport(
            overall_status=ValidationStatus.PASSED,
            issues=[],
            tables_validated=len(tables),
            tables_passed=0,
            tables_with_warnings=0,
            tables_failed=0,
        )

        if not table_names:
            table_names = [f"Table_{i+1}" for i in range(len(tables))]

        for table, table_name in zip(tables, table_names):
            table_status = self._validate_single_table(table, table_name, report)

            if table_status == ValidationStatus.PASSED:
                report.tables_passed += 1
            elif table_status == ValidationStatus.WARNING:
                report.tables_with_warnings += 1
            elif table_status == ValidationStatus.FAILED:
                report.tables_failed += 1

        return report

    def _validate_single_table(
        self, table: ExtractedTable, table_name: str, report: ValidationReport
    ) -> ValidationStatus:
        """
        Validate a single table.

        Args:
            table: Table to validate
            table_name: Name for error reporting
            report: Validation report to update

        Returns:
            Worst validation status for this table
        """
        worst_status = ValidationStatus.PASSED

        # Generic validations
        status = self._validate_no_duplicate_rows(table, table_name, report)
        worst_status = self._update_worst_status(worst_status, status)

        status = self._validate_column_consistency(table, table_name, report)
        worst_status = self._update_worst_status(worst_status, status)

        status = self._validate_header_before_data(table, table_name, report)
        worst_status = self._update_worst_status(worst_status, status)

        # Detect table type for specific validations
        if self._is_distribution_table(table):
            status = self._validate_distribution_table(table, table_name, report)
            worst_status = self._update_worst_status(worst_status, status)

        if self._is_roster_table(table):
            status = self._validate_roster_table(table, table_name, report)
            worst_status = self._update_worst_status(worst_status, status)

        return worst_status

    def _validate_no_duplicate_rows(
        self, table: ExtractedTable, table_name: str, report: ValidationReport
    ) -> ValidationStatus:
        """Validate no duplicate rows (except header)."""
        if table.is_empty or len(table.data) <= 1:
            return ValidationStatus.PASSED

        seen_rows = set()
        data_rows = table.data[1:] if table.schema.has_header else table.data

        for idx, row in enumerate(data_rows):
            row_tuple = tuple(str(cell).strip() for cell in row)

            if row_tuple in seen_rows and any(row_tuple):  # Ignore empty rows
                report.add_issue(
                    ValidationIssue(
                        severity=ValidationStatus.FAILED,
                        message=f"Duplicate row found",
                        table_name=table_name,
                        row_index=idx + (1 if table.schema.has_header else 0),
                        details={"row_content": list(row_tuple)},
                    )
                )
                return ValidationStatus.FAILED

            seen_rows.add(row_tuple)

        return ValidationStatus.PASSED

    def _validate_column_consistency(
        self, table: ExtractedTable, table_name: str, report: ValidationReport
    ) -> ValidationStatus:
        """Validate consistent column count across all rows."""
        if table.is_empty:
            return ValidationStatus.PASSED

        expected_cols = table.schema.column_count
        status = ValidationStatus.PASSED

        for idx, row in enumerate(table.data):
            if len(row) != expected_cols:
                report.add_issue(
                    ValidationIssue(
                        severity=ValidationStatus.WARNING,
                        message=f"Inconsistent column count: expected {expected_cols}, got {len(row)}",
                        table_name=table_name,
                        row_index=idx,
                        details={"expected": expected_cols, "actual": len(row)},
                    )
                )
                status = ValidationStatus.WARNING

        return status

    def _validate_header_before_data(
        self, table: ExtractedTable, table_name: str, report: ValidationReport
    ) -> ValidationStatus:
        """Validate header comes before data (for rosters)."""
        if not table.schema.has_header and len(table.data) > 0:
            report.add_issue(
                ValidationIssue(
                    severity=ValidationStatus.WARNING,
                    message="Table has no detected header",
                    table_name=table_name,
                    details={"rows": len(table.data)},
                )
            )
            return ValidationStatus.WARNING

        return ValidationStatus.PASSED

    def _validate_distribution_table(
        self, table: ExtractedTable, table_name: str, report: ValidationReport
    ) -> ValidationStatus:
        """
        Validate statistical distribution table.

        Checks:
        - Percent totals = 100.00 ± tolerance
        - Non-negative frequencies
        - Monotonic cumulative frequency
        - Score ranges match domain
        """
        status = ValidationStatus.PASSED

        # Find percent and cumulative columns
        percent_col_idx = self._find_column_index(
            table.schema.headers, ["percent", "percentage", "%"]
        )
        cumulative_col_idx = self._find_column_index(
            table.schema.headers, ["cumulative", "cum", "cum."]
        )
        frequency_col_idx = self._find_column_index(
            table.schema.headers, ["frequency", "freq", "f"]
        )
        score_col_idx = self._find_column_index(
            table.schema.headers, ["score", "mark", "grade"]
        )

        # Validate percent total = 100
        if percent_col_idx is not None:
            percent_total = self._sum_column(table, percent_col_idx)

            if percent_total is not None:
                if abs(percent_total - 100.0) > self.tolerance * 100:
                    report.add_issue(
                        ValidationIssue(
                            severity=ValidationStatus.FAILED,
                            message=f"Percent column does not sum to 100.00 (got {percent_total:.2f})",
                            table_name=table_name,
                            column_name=table.schema.headers[percent_col_idx],
                            details={
                                "expected": 100.0,
                                "actual": percent_total,
                                "tolerance": self.tolerance * 100,
                            },
                        )
                    )
                    status = ValidationStatus.FAILED

        # Validate non-negative frequencies
        if frequency_col_idx is not None:
            for idx, row in enumerate(table.data[1:], start=1):
                if len(row) > frequency_col_idx:
                    freq_val = self._extract_number(row[frequency_col_idx])
                    if freq_val is not None and freq_val < 0:
                        report.add_issue(
                            ValidationIssue(
                                severity=ValidationStatus.FAILED,
                                message=f"Negative frequency found: {freq_val}",
                                table_name=table_name,
                                row_index=idx,
                                column_name=table.schema.headers[frequency_col_idx],
                            )
                        )
                        status = ValidationStatus.FAILED

        # Validate monotonic cumulative frequency
        if cumulative_col_idx is not None:
            prev_cumulative = None

            for idx, row in enumerate(table.data[1:], start=1):
                if len(row) > cumulative_col_idx:
                    cum_val = self._extract_number(row[cumulative_col_idx])

                    if cum_val is not None:
                        if prev_cumulative is not None and cum_val < prev_cumulative:
                            report.add_issue(
                                ValidationIssue(
                                    severity=ValidationStatus.FAILED,
                                    message=f"Cumulative frequency not monotonic: {cum_val} < {prev_cumulative}",
                                    table_name=table_name,
                                    row_index=idx,
                                    column_name=table.schema.headers[cumulative_col_idx],
                                )
                            )
                            status = ValidationStatus.FAILED

                        prev_cumulative = cum_val

        # Validate score domain if specified
        if table.score_domain and score_col_idx is not None:
            for idx, row in enumerate(table.data[1:], start=1):
                if len(row) > score_col_idx:
                    score_val = self._extract_number(row[score_col_idx])

                    if score_val is not None:
                        if not (
                            table.score_domain.min_score
                            <= score_val
                            <= table.score_domain.max_score
                        ):
                            report.add_issue(
                                ValidationIssue(
                                    severity=ValidationStatus.WARNING,
                                    message=f"Score {score_val} outside domain range [{table.score_domain.min_score}, {table.score_domain.max_score}]",
                                    table_name=table_name,
                                    row_index=idx,
                                    column_name=table.schema.headers[score_col_idx],
                                )
                            )
                            status = self._update_worst_status(
                                status, ValidationStatus.WARNING
                            )

        return status

    def _validate_roster_table(
        self, table: ExtractedTable, table_name: str, report: ValidationReport
    ) -> ValidationStatus:
        """
        Validate roster table (staff list, student list, etc.).

        Checks:
        - No orphan rows
        - Column count consistency
        - Header detected
        """
        status = ValidationStatus.PASSED

        # Already checked header and column consistency in generic validations

        # Check for orphan rows (single-cell rows that aren't section titles)
        for idx, row in enumerate(table.data):
            non_empty_cells = [cell for cell in row if str(cell).strip()]

            if len(non_empty_cells) == 1 and idx > 0:
                # Could be section title or orphan
                # Section titles are OK, but isolated cells are suspicious
                if idx < len(table.data) - 1:
                    next_row = table.data[idx + 1]
                    next_non_empty = [cell for cell in next_row if str(cell).strip()]

                    if len(next_non_empty) == 1:
                        # Two single-cell rows in a row = likely orphan
                        report.add_issue(
                            ValidationIssue(
                                severity=ValidationStatus.WARNING,
                                message="Possible orphan row detected",
                                table_name=table_name,
                                row_index=idx,
                                details={"content": row[0]},
                            )
                        )
                        status = ValidationStatus.WARNING

        return status

    @staticmethod
    def _is_distribution_table(table: ExtractedTable) -> bool:
        """Detect if table is a statistical distribution table."""
        if table.is_empty:
            return False

        headers_lower = [h.lower() for h in table.schema.headers]

        # Look for distribution table indicators
        indicators = ["frequency", "percent", "cumulative", "score", "mark"]
        matches = sum(1 for indicator in indicators if any(indicator in h for h in headers_lower))

        return matches >= 2

    @staticmethod
    def _is_roster_table(table: ExtractedTable) -> bool:
        """Detect if table is a roster/list table."""
        if table.is_empty:
            return False

        headers_lower = [h.lower() for h in table.schema.headers]

        # Look for roster indicators
        indicators = ["name", "position", "department", "staff", "student", "employee"]
        return any(indicator in " ".join(headers_lower) for indicator in indicators)

    @staticmethod
    def _find_column_index(headers: List[str], keywords: List[str]) -> Optional[int]:
        """Find column index by keyword match."""
        headers_lower = [h.lower() for h in headers]

        for idx, header in enumerate(headers_lower):
            for keyword in keywords:
                if keyword in header:
                    return idx

        return None

    @staticmethod
    def _sum_column(table: ExtractedTable, col_idx: int) -> Optional[float]:
        """Sum numeric values in a column."""
        total = 0.0
        count = 0

        for row in table.data[1:]:  # Skip header
            if len(row) > col_idx:
                val = TableValidator._extract_number(row[col_idx])
                if val is not None:
                    total += val
                    count += 1

        return total if count > 0 else None

    @staticmethod
    def _extract_number(value: any) -> Optional[float]:
        """Extract numeric value from cell."""
        if value is None:
            return None

        try:
            cleaned = str(value).replace(",", "").replace("%", "").strip()
            return float(cleaned)
        except (ValueError, AttributeError):
            return None

    @staticmethod
    def _update_worst_status(
        current: ValidationStatus, new: ValidationStatus
    ) -> ValidationStatus:
        """Update to worst status."""
        priority = {
            ValidationStatus.PASSED: 0,
            ValidationStatus.WARNING: 1,
            ValidationStatus.FAILED: 2,
        }

        if priority[new] > priority[current]:
            return new
        return current
