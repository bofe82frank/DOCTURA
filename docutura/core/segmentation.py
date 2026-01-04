"""
Table segmentation strategies for DocTura Desktop.

Implements score-domain and header-repetition segmentation
to prevent page-boundary truncation issues.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from docutura.core.models import (
    ExtractedTable,
    ScoreDomain,
    SegmentationStrategy,
    TableSchema,
)


class TableSegmenter:
    """
    Segments tables using domain-specific strategies.

    This is critical to prevent the TASS Scaled Essay truncation incident.
    """

    def __init__(self):
        self.strategies = {
            SegmentationStrategy.SCORE_DOMAIN: self.segment_by_score_domain,
            SegmentationStrategy.HEADER_REPETITION: self.segment_by_header_repetition,
        }

    def segment_tables(
        self,
        all_tables: List[Dict[str, Any]],
        strategy: SegmentationStrategy,
        score_domains: Optional[List[ScoreDomain]] = None,
    ) -> List[ExtractedTable]:
        """
        Segment tables using specified strategy.

        Args:
            all_tables: All extracted tables (from all pages)
            strategy: Segmentation strategy to use
            score_domains: Score domain definitions (for score-domain strategy)

        Returns:
            List of logically segmented tables
        """
        if strategy == SegmentationStrategy.AUTO:
            # Try to detect which strategy to use
            strategy = self._detect_strategy(all_tables)

        handler = self.strategies.get(strategy)
        if not handler:
            raise ValueError(f"Unknown segmentation strategy: {strategy}")

        return handler(all_tables, score_domains=score_domains)

    def _detect_strategy(
        self, all_tables: List[Dict[str, Any]]
    ) -> SegmentationStrategy:
        """
        Auto-detect appropriate segmentation strategy.

        Args:
            all_tables: All extracted tables

        Returns:
            Detected strategy
        """
        # Check for score columns (numbers in first column)
        has_score_column = False
        for table_dict in all_tables:
            data = table_dict.get("data", [])
            if data and len(data) > 1:
                first_col_values = [row[0] for row in data[1:] if row]
                numeric_count = sum(
                    1 for val in first_col_values if self._is_numeric(val)
                )
                if numeric_count > len(first_col_values) * 0.7:  # 70% numeric
                    has_score_column = True
                    break

        if has_score_column:
            return SegmentationStrategy.SCORE_DOMAIN

        # Check for repeated headers
        headers = []
        for table_dict in all_tables:
            data = table_dict.get("data", [])
            if data:
                first_row = tuple(data[0])
                if first_row in headers:
                    return SegmentationStrategy.HEADER_REPETITION
                headers.append(first_row)

        # Default to header repetition
        return SegmentationStrategy.HEADER_REPETITION

    def segment_by_score_domain(
        self,
        all_tables: List[Dict[str, Any]],
        score_domains: Optional[List[ScoreDomain]] = None,
    ) -> List[ExtractedTable]:
        """
        Segment tables by score domains.

        This prevents truncation when score ranges span page boundaries.
        Example: Scaled Essay (15-40) should not be split across pages.

        Args:
            all_tables: All extracted tables
            score_domains: Score domain definitions

        Returns:
            Logically segmented tables by score domain
        """
        if not score_domains:
            # Use default domains if not specified
            score_domains = self._detect_score_domains(all_tables)

        # Merge all data first (ignore page boundaries)
        merged_data = []
        source_pages = []

        for table_dict in all_tables:
            data = table_dict.get("data", [])
            page = table_dict.get("page", 1)

            merged_data.extend(data)
            if page not in source_pages:
                source_pages.append(page)

        if not merged_data:
            return []

        # Extract header
        header = merged_data[0] if merged_data else []
        data_rows = merged_data[1:] if len(merged_data) > 1 else []

        # Find score column (usually first column)
        score_col_idx = 0  # Default to first column

        # Segment by score domains
        segmented_tables = []

        for domain in score_domains:
            domain_rows = []

            for row in data_rows:
                if not row or len(row) <= score_col_idx:
                    continue

                score_val = row[score_col_idx]
                score_num = self._extract_number(score_val)

                if score_num is not None and domain.min_score <= score_num <= domain.max_score:
                    domain_rows.append(row)

            if domain_rows:
                # Create table for this domain
                table_data = [header] + domain_rows

                schema = TableSchema(
                    headers=header,
                    column_count=len(header),
                    has_header=True,
                    header_row_indices=[0],
                )

                table = ExtractedTable(
                    data=table_data,
                    schema=schema,
                    source_pages=source_pages,
                    table_type="logical",
                    segmentation_strategy=SegmentationStrategy.SCORE_DOMAIN,
                    score_domain=domain,
                )

                segmented_tables.append(table)

        return segmented_tables

    def segment_by_header_repetition(
        self,
        all_tables: List[Dict[str, Any]],
        score_domains: Optional[List[ScoreDomain]] = None,
    ) -> List[ExtractedTable]:
        """
        Segment tables by repeated headers.

        This is useful for rosters and lists where section headers repeat.
        Example: International Staff List with department headers.

        Args:
            all_tables: All extracted tables
            score_domains: Not used for this strategy

        Returns:
            Logically segmented tables by header groups
        """
        if not all_tables:
            return []

        # Merge all data across pages
        merged_data = []
        source_pages = []

        for table_dict in all_tables:
            data = table_dict.get("data", [])
            page = table_dict.get("page", 1)

            merged_data.extend(data)
            if page not in source_pages:
                source_pages.append(page)

        if not merged_data:
            return []

        # Detect headers and section titles
        header_pattern = self._detect_header_pattern(all_tables)

        if not header_pattern:
            # No repeated headers, treat as single table
            return self._create_single_logical_table(merged_data, source_pages)

        # Segment by header occurrences
        segmented_tables = []
        current_section = []
        current_header = None
        section_title = None

        for row in merged_data:
            if not row:
                continue

            # Check if this row is a header
            if self._is_header_row(row, header_pattern):
                # Save previous section if exists
                if current_section and current_header:
                    table = self._create_table_from_section(
                        current_header, current_section, source_pages, section_title
                    )
                    if table:
                        segmented_tables.append(table)

                # Start new section
                current_header = row
                current_section = []
                section_title = None

            # Check if this row is a section title
            elif self._is_section_title(row):
                section_title = row[0] if row else None

            # Regular data row
            else:
                if current_header is not None:
                    current_section.append(row)

        # Save last section
        if current_section and current_header:
            table = self._create_table_from_section(
                current_header, current_section, source_pages, section_title
            )
            if table:
                segmented_tables.append(table)

        # If no segmentation occurred, return single table
        if not segmented_tables:
            return self._create_single_logical_table(merged_data, source_pages)

        return segmented_tables

    def _detect_score_domains(
        self, all_tables: List[Dict[str, Any]]
    ) -> List[ScoreDomain]:
        """
        Auto-detect score domains from data.

        Args:
            all_tables: All extracted tables

        Returns:
            List of detected score domains
        """
        # Extract all score values from first column
        scores = []

        for table_dict in all_tables:
            data = table_dict.get("data", [])
            for row in data[1:]:  # Skip header
                if row:
                    score_num = self._extract_number(row[0])
                    if score_num is not None:
                        scores.append(score_num)

        if not scores:
            return []

        # Find natural breaks in score distribution
        scores = sorted(set(scores))

        # Simple heuristic: split at gaps > 5
        domains = []
        current_min = scores[0]

        for i in range(1, len(scores)):
            if scores[i] - scores[i - 1] > 5:
                # Gap detected, create domain
                domains.append(
                    ScoreDomain(
                        name=f"Score Range {current_min}-{scores[i-1]}",
                        min_score=int(current_min),
                        max_score=int(scores[i - 1]),
                    )
                )
                current_min = scores[i]

        # Add final domain
        domains.append(
            ScoreDomain(
                name=f"Score Range {current_min}-{scores[-1]}",
                min_score=int(current_min),
                max_score=int(scores[-1]),
            )
        )

        return domains

    def _detect_header_pattern(
        self, all_tables: List[Dict[str, Any]]
    ) -> Optional[Tuple[str, ...]]:
        """
        Detect repeated header pattern.

        Args:
            all_tables: All extracted tables

        Returns:
            Header pattern tuple, or None if no pattern found
        """
        header_counts: Dict[Tuple[str, ...], int] = {}

        for table_dict in all_tables:
            data = table_dict.get("data", [])
            for row in data:
                if row and all(cell.strip() for cell in row):
                    # This could be a header
                    row_tuple = tuple(cell.strip().upper() for cell in row)
                    header_counts[row_tuple] = header_counts.get(row_tuple, 0) + 1

        # Find most repeated pattern (appears 2+ times)
        for pattern, count in header_counts.items():
            if count >= 2:
                return pattern

        return None

    def _is_header_row(
        self, row: List[str], header_pattern: Tuple[str, ...]
    ) -> bool:
        """Check if row matches header pattern."""
        if not row or len(row) != len(header_pattern):
            return False

        row_tuple = tuple(cell.strip().upper() for cell in row)
        return row_tuple == header_pattern

    def _is_section_title(self, row: List[str]) -> bool:
        """
        Check if row is a section title.

        Section titles typically have text in first cell only.
        """
        if not row or len(row) < 2:
            return False

        first_cell = row[0].strip()
        other_cells = [cell.strip() for cell in row[1:]]

        return bool(first_cell) and all(not cell for cell in other_cells)

    def _create_table_from_section(
        self,
        header: List[str],
        section_data: List[List[str]],
        source_pages: List[int],
        section_title: Optional[str] = None,
    ) -> Optional[ExtractedTable]:
        """Create ExtractedTable from section data."""
        if not section_data:
            return None

        table_data = [header] + section_data

        schema = TableSchema(
            headers=header,
            column_count=len(header),
            has_header=True,
            header_row_indices=[0],
        )

        return ExtractedTable(
            data=table_data,
            schema=schema,
            source_pages=source_pages,
            table_type="logical",
            segmentation_strategy=SegmentationStrategy.HEADER_REPETITION,
            section_title=section_title,
        )

    def _create_single_logical_table(
        self, data: List[List[str]], source_pages: List[int]
    ) -> List[ExtractedTable]:
        """Create a single logical table from all data."""
        if not data:
            return []

        # Assume first row is header
        header = data[0] if data else []
        rows = data[1:] if len(data) > 1 else []

        schema = TableSchema(
            headers=header,
            column_count=len(header) if header else 0,
            has_header=True,
            header_row_indices=[0],
        )

        table = ExtractedTable(
            data=data,
            schema=schema,
            source_pages=source_pages,
            table_type="logical",
        )

        return [table]

    @staticmethod
    def _is_numeric(value: str) -> bool:
        """Check if value is numeric."""
        try:
            float(str(value).replace(",", "").strip())
            return True
        except (ValueError, AttributeError):
            return False

    @staticmethod
    def _extract_number(value: Any) -> Optional[float]:
        """Extract numeric value from string."""
        if value is None:
            return None

        try:
            # Remove commas and whitespace
            cleaned = str(value).replace(",", "").strip()
            return float(cleaned)
        except (ValueError, AttributeError):
            return None
