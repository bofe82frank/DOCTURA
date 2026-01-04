"""
International Staff List Plugin.

Handles roster-style documents with repeated headers and section grouping.
"""

import re
from typing import Any, Dict, List, Optional

from docutura.core.models import DocumentMetadata, SegmentationStrategy
from docutura.plugins.base import DocumentPlugin, PluginDetectionResult


class InternationalStaffListPlugin(DocumentPlugin):
    """Plugin for international staff list documents."""

    def get_plugin_id(self) -> str:
        return "international_staff_list"

    def get_version(self) -> str:
        return "1.0.0"

    def detect(
        self,
        tables_data: List[Dict[str, Any]],
        page_texts: List[str],
        context: Dict[str, Any],
    ) -> PluginDetectionResult:
        """
        Detect if document is an international staff list.

        Looks for:
        - "STAFF" keyword
        - "INTERNATIONAL" keyword
        - Repeated table headers (Name, Position, Department, etc.)
        - Section titles (department names)
        """
        confidence = 0.0
        metadata = {}

        # Join all page texts
        full_text = " ".join(page_texts).upper()

        # Check for staff list indicators
        staff_indicators = ["STAFF LIST", "STAFF ROSTER", "INTERNATIONAL STAFF", "PERSONNEL"]
        indicator_matches = sum(1 for ind in staff_indicators if ind in full_text)

        if indicator_matches > 0:
            confidence += 0.3 * min(indicator_matches, 2)

        # Check for roster-style headers
        roster_keywords = ["NAME", "POSITION", "DEPARTMENT", "NATIONALITY"]
        keyword_count = 0

        for table_dict in tables_data:
            data = table_dict.get("data", [])
            if data:
                first_row = " ".join(str(cell).upper() for cell in data[0])
                keyword_count += sum(1 for kw in roster_keywords if kw in first_row)

        if keyword_count >= 2:  # At least 2 of the keywords
            confidence += 0.3

        # Check for repeated headers (indicates header-based segmentation)
        header_pattern = self._find_repeated_header(tables_data)
        if header_pattern:
            confidence += 0.4
            metadata["header_pattern"] = list(header_pattern)

        # Extract year if present
        year_match = re.search(r"\b(20\d{2})\b", full_text)
        if year_match:
            metadata["year"] = year_match.group(1)

        return PluginDetectionResult(
            plugin_id=self.plugin_id, confidence=min(confidence, 1.0), metadata=metadata
        )

    def get_segmentation_strategy(self) -> SegmentationStrategy:
        """Use header-repetition segmentation for rosters."""
        return SegmentationStrategy.HEADER_REPETITION

    def extract_metadata(
        self,
        tables_data: List[Dict[str, Any]],
        page_texts: List[str],
        context: Dict[str, Any],
    ) -> DocumentMetadata:
        """Extract staff list metadata."""
        full_text = " ".join(page_texts)

        # Extract title
        title_match = re.search(
            r"(INTERNATIONAL\s+STAFF\s+LIST.*?(?:\d{4})?)", full_text, re.IGNORECASE
        )
        title = title_match.group(1).strip() if title_match else "International Staff List"

        # Extract organization
        org_match = re.search(
            r"(?:SCHOOL|COLLEGE|UNIVERSITY|ORGANIZATION)[:\s]+([A-Z\s&]+)",
            full_text,
            re.IGNORECASE,
        )
        organization = org_match.group(1).strip() if org_match else None

        # Extract year
        year_match = re.search(r"\b(20\d{2})\b", full_text)
        year = year_match.group(1) if year_match else None

        return DocumentMetadata(
            title=title,
            organization=organization,
            reporting_period=year,
            plugin_id=self.plugin_id,
            plugin_version=self.version,
        )

    def _find_repeated_header(
        self, tables_data: List[Dict[str, Any]]
    ) -> Optional[tuple]:
        """Find repeated header pattern in tables."""
        header_counts: Dict[tuple, int] = {}

        for table_dict in tables_data:
            data = table_dict.get("data", [])
            for row in data:
                if row and all(cell and str(cell).strip() for cell in row):
                    row_tuple = tuple(str(cell).strip().upper() for cell in row)
                    header_counts[row_tuple] = header_counts.get(row_tuple, 0) + 1

        # Find most repeated pattern (appears 2+ times)
        for pattern, count in header_counts.items():
            if count >= 2:
                return pattern

        return None

    def summarize(self, tables: List["ExtractedTable"]) -> Optional[str]:
        """Generate summary of staff list data."""
        summaries = []

        total_staff = 0
        for table in tables:
            section_name = table.section_title or "General"
            count = table.row_count - 1  # Exclude header
            total_staff += count
            summaries.append(f"- {section_name}: {count} staff members")

        if summaries:
            return (
                f"International Staff List Summary:\n"
                f"Total Staff: {total_staff}\n\n"
                f"By Section:\n" + "\n".join(summaries)
            )

        return None
